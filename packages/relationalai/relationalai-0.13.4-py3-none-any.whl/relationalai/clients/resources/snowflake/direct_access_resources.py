"""
Direct Access Resources - Resources class for Direct Service Access.
This class overrides methods to use direct HTTP requests instead of Snowflake service functions.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import requests

from .... import debugging
from ....tools.constants import USE_GRAPH_INDEX, DEFAULT_QUERY_TIMEOUT_MINS, Generation
from ....environments import runtime_env, SnowbookEnvironment
from ...config import Config, ConfigStore, ENDPOINT_FILE
from ...direct_access_client import DirectAccessClient
from ...types import EngineState
from ...util import get_pyrel_version, safe_json_loads, ms_to_timestamp
from ....errors import GuardRailsException, ResponseStatusException, QueryTimeoutExceededException, RAIException
from snowflake.snowpark import Session

# Import UseIndexResources to enable use_index functionality with direct access
from .use_index_resources import UseIndexResources
from .snowflake import TxnCreationResult

# Import helper functions from util
from .util import is_engine_issue as _is_engine_issue, is_database_issue as _is_database_issue, collect_error_messages

from .use_index_poller import DirectUseIndexPoller
from typing import Iterable

# Constants
TXN_ABORT_REASON_TIMEOUT = "transaction timeout"
TXN_ABORT_REASON_GUARD_RAILS = "guard rail violation"


class DirectAccessResources(UseIndexResources):
    """
    Resources class for Direct Service Access avoiding Snowflake service functions.
    Uses HTTP requests instead of Snowflake SQL for execution.
    """
    def __init__(
        self,
        profile: Union[str, None] = None,
        config: Union[Config, None] = None,
        connection: Union[Session, None] = None,
        dry_run: bool = False,
        reset_session: bool = False,
        generation: Optional[Generation] = None,
        language: str = "rel",
    ):
        super().__init__(
            generation=generation,
            profile=profile,
            config=config,
            connection=connection,
            reset_session=reset_session,
            dry_run=dry_run,
            language=language,
        )
        self._endpoint_info = ConfigStore(ENDPOINT_FILE)
        self._service_endpoint = ""
        self._direct_access_client = None
        # database and language are already set by UseIndexResources.__init__

    @property
    def service_endpoint(self) -> str:
        return self._retrieve_service_endpoint()

    def _retrieve_service_endpoint(self, enforce_update=False) -> str:
        account = self.config.get("account")
        app_name = self.config.get("rai_app_name")
        service_endpoint_key = f"{account}.{app_name}.service_endpoint"
        if self._service_endpoint and not enforce_update:
            return self._service_endpoint
        if self._endpoint_info.get(service_endpoint_key, "") and not enforce_update:
            self._service_endpoint = str(self._endpoint_info.get(service_endpoint_key, ""))
            return self._service_endpoint

        is_snowflake_notebook = isinstance(runtime_env, SnowbookEnvironment)
        query = f"CALL {self.get_app_name()}.app.service_endpoint({not is_snowflake_notebook});"
        result = self._exec(query)
        assert result, f"Could not retrieve service endpoint for {self.get_app_name()}"
        if is_snowflake_notebook:
            self._service_endpoint = f"http://{result[0]['SERVICE_ENDPOINT']}"
        else:
            self._service_endpoint = f"https://{result[0]['SERVICE_ENDPOINT']}"

        self._endpoint_info.set(service_endpoint_key, self._service_endpoint)
        # save the endpoint to `ENDPOINT_FILE` to avoid calling the endpoint with every
        # pyrel execution
        try:
            self._endpoint_info.save()
        except Exception:
            print("Failed to persist endpoints to file. This might slow down future executions.")

        return self._service_endpoint

    @property
    def direct_access_client(self) -> DirectAccessClient:
        if self._direct_access_client:
            return self._direct_access_client
        try:
            service_endpoint = self.service_endpoint
            self._direct_access_client = DirectAccessClient(
                self.config, self.token_handler, service_endpoint, self.generation,
            )
        except Exception as e:
            raise e
        return self._direct_access_client

    def request(
        self,
        endpoint: str,
        payload: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        path_params: Dict[str, str] | None = None,
        query_params: Dict[str, str] | None = None,
        skip_auto_create: bool = False,
        skip_engine_db_error_retry: bool = False,
    ) -> requests.Response:
        with debugging.span("direct_access_request"):
            def _send_request():
                return self.direct_access_client.request(
                    endpoint=endpoint,
                    payload=payload,
                    headers=headers,
                    path_params=path_params,
                    query_params=query_params,
                )
            try:
                response = _send_request()
                if response.status_code != 200:
                    # For 404 responses with skip_auto_create=True, return immediately to let caller handle it
                    # (e.g., get_engine needs to check 404 and return None for auto_create_engine)
                    # For skip_auto_create=False, continue to auto-creation logic below
                    if response.status_code == 404 and skip_auto_create:
                        return response

                    try:
                        message = response.json().get("message", "")
                    except requests.exceptions.JSONDecodeError:
                        # Can't parse JSON response. For skip_auto_create=True (e.g., get_engine),
                        # this should have been caught by the 404 check above, so this is an error.
                        # For skip_auto_create=False, we explicitly check status_code below,
                        # so we don't need to parse the message.
                        if skip_auto_create:
                            raise ResponseStatusException(
                                f"Failed to parse error response from endpoint {endpoint}.", response
                            )
                        message = ""  # Not used when we check status_code directly

                    # fix engine on engine error and retry
                    # Skip setting up GI if skip_auto_create is True to avoid recursion or skip_engine_db_error_retry is true to let _exec_async_v2 perform the retry with the correct headers.
                    if ((_is_engine_issue(message) and not skip_auto_create) or _is_database_issue(message)) and not skip_engine_db_error_retry:
                        engine_name = payload.get("caller_engine_name", "") if payload else ""
                        engine_name = engine_name or self.get_default_engine_name()
                        engine_size = self.config.get_default_engine_size()
                        # Use the mixin's _poll_use_index method
                        self._poll_use_index(
                            app_name=self.get_app_name(),
                            sources=self.sources,
                            model=self.database,
                            engine_name=engine_name,
                            engine_size=engine_size,
                            headers=headers,
                        )
                        response = _send_request()
            except (requests.exceptions.ConnectionError, RAIException) as e:
                messages = collect_error_messages(e)
                if any("nameresolutionerror" in msg for msg in messages) or \
                   any("could not find the service associated with endpoint" in msg for msg in messages):
                    # when we can not resolve the service endpoint or the service is not found,
                    # we assume the endpoint is outdated, so we retrieve it again and retry.
                    self.direct_access_client.service_endpoint = self._retrieve_service_endpoint(
                        enforce_update=True,
                    )
                    return _send_request()
                # raise in all other cases
                raise e
            return response

    def _txn_request_with_gi_retry(
        self,
        payload: Dict,
        headers: Dict[str, str],
        query_params: Dict,
        engine: Union[str, None],
    ):
        """Make request with graph index retry logic.

        Attempts request with gi_setup_skipped=True first. If an engine or database
        issue occurs, polls use_index and retries with gi_setup_skipped=False.
        """
        response = self.request(
            "create_txn", payload=payload, headers=headers, query_params=query_params, skip_auto_create=True, skip_engine_db_error_retry=True
        )

        if response.status_code != 200:
            try:
                message = response.json().get("message", "")
            except requests.exceptions.JSONDecodeError:
                message = ""

            if _is_engine_issue(message) or _is_database_issue(message):
                engine_name = engine or self.get_default_engine_name()
                engine_size = self.config.get_default_engine_size()
                # Use the mixin's _poll_use_index method
                self._poll_use_index(
                    app_name=self.get_app_name(),
                    sources=self.sources,
                    model=self.database,
                    engine_name=engine_name,
                    engine_size=engine_size,
                    headers=headers,
                )
                headers['gi_setup_skipped'] = 'False'
                response = self.request(
                    "create_txn", payload=payload, headers=headers, query_params=query_params, skip_auto_create=True, skip_engine_db_error_retry=True
                )
            else:
                raise ResponseStatusException("Failed to create transaction.", response)

        return response

    def _create_v2_txn(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        inputs: Dict,
        headers: Dict[str, str],
        readonly: bool,
        nowait_durable: bool,
        bypass_index: bool,
        language: str,
        query_timeout_mins: int | None,
    ) -> TxnCreationResult:
        """
        Create a transaction via direct HTTP access and return the result.

        This override uses HTTP requests instead of SQL stored procedures.
        """
        use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)

        payload = {
            "dbname": database,
            "engine_name": engine,
            "query": raw_code,
            "v1_inputs": inputs,
            "nowait_durable": nowait_durable,
            "readonly": readonly,
            "language": language,
        }
        if query_timeout_mins is None and (timeout_value := self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
            query_timeout_mins = int(timeout_value)
        if query_timeout_mins is not None:
            payload["timeout_mins"] = query_timeout_mins
        query_params = {"use_graph_index": str(use_graph_index and not bypass_index)}

        response = self._txn_request_with_gi_retry(
            payload, headers, query_params, engine
        )

        response_content = response.json()

        txn_id = response_content["transaction"]['id']
        state = response_content["transaction"]['state']

        # Build artifact_info if transaction completed immediately (fast path)
        artifact_info: Dict[str, Dict] = {}
        if state in ["COMPLETED", "ABORTED"]:
            for result in response_content.get("results", []):
                filename = result['filename']
                # making keys uppercase to match the old behavior
                artifact_info[filename] = {k.upper(): v for k, v in result.items()}

        return TxnCreationResult(txn_id=txn_id, state=state, artifact_info=artifact_info)

    def _prepare_index(
        self,
        model: str,
        engine_name: str,
        engine_size: str = "",
        language: str = "rel",
        rai_relations: List[str] | None = None,
        pyrel_program_id: str | None  = None,
        skip_pull_relations: bool = False,
        headers: Dict | None = None,
    ):
        """
        Prepare the index for the given engine and model.
        """
        with debugging.span("prepare_index"):
            if headers is None:
                headers = {}

            payload = {
                "model_name": model,
                "caller_engine_name": engine_name,
                "language": language,
                "pyrel_program_id": pyrel_program_id,
                "skip_pull_relations": skip_pull_relations,
                "rai_relations": rai_relations or [],
                "user_agent": get_pyrel_version(self.generation),
            }
            # Only include engine_size if it has a non-empty string value
            if engine_size and engine_size.strip():
                payload["caller_engine_size"] = engine_size

            response = self.request(
                "prepare_index", payload=payload, headers=headers
            )

            if response.status_code != 200:
                raise ResponseStatusException("Failed to prepare index.", response)

            return response.json()

    def _check_exec_async_status(self, txn_id: str, headers: Dict[str, str] | None = None) -> bool:
        """Check whether the given transaction has completed."""

        with debugging.span("check_status"):
            response = self.request(
                "get_txn",
                headers=headers,
                path_params={"txn_id": txn_id},
            )
            assert response, f"No results from get_transaction('{txn_id}')"

        response_content = response.json()
        transaction = response_content["transaction"]
        status: str = transaction['state']

        # remove the transaction from the pending list if it's completed or aborted
        if status in ["COMPLETED", "ABORTED"]:
            if txn_id in self._pending_transactions:
                self._pending_transactions.remove(txn_id)

        if status == "ABORTED":
            reason = transaction.get("abort_reason", "")

            if reason == TXN_ABORT_REASON_TIMEOUT:
                config_file_path = getattr(self.config, 'file_path', None)
                timeout_ms = int(transaction.get("timeout_ms", 0))
                timeout_mins = timeout_ms // 60000 if timeout_ms > 0 else int(self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS) or DEFAULT_QUERY_TIMEOUT_MINS)
                raise QueryTimeoutExceededException(
                    timeout_mins=timeout_mins,
                    query_id=txn_id,
                    config_file_path=config_file_path,
                )
            elif reason == TXN_ABORT_REASON_GUARD_RAILS:
                raise GuardRailsException(response_content.get("progress", {}))

        # @TODO: Find some way to tunnel the ABORT_REASON out. Azure doesn't have this, but it's handy
        return status == "COMPLETED" or status == "ABORTED"

    def _list_exec_async_artifacts(self, txn_id: str, headers: Dict[str, str] | None = None) -> Dict[str, Dict]:
        """Grab the list of artifacts produced in the transaction and the URLs to retrieve their contents."""
        with debugging.span("list_results"):
            response = self.request(
                "get_txn_artifacts",
                headers=headers,
                path_params={"txn_id": txn_id},
            )
            assert response, f"No results from get_transaction_artifacts('{txn_id}')"
            artifact_info = {}
            for result in response.json()["results"]:
                filename = result['filename']
                # making keys uppercase to match the old behavior
                artifact_info[filename] = {k.upper(): v for k, v in result.items()}
            return artifact_info

    def get_transaction_problems(self, txn_id: str) -> List[Dict[str, Any]]:
        with debugging.span("get_transaction_problems"):
            response = self.request(
                "get_txn_problems",
                path_params={"txn_id": txn_id},
            )
            response_content = response.json()
            if not response_content:
                return []
            return response_content.get("problems", [])

    def get_transaction_events(self, transaction_id: str, continuation_token: str = ''):
        response = self.request(
            "get_txn_events",
            path_params={"txn_id": transaction_id, "stream_name": "profiler"},
            query_params={"continuation_token": continuation_token},
        )
        response_content = response.json()
        if not response_content:
            return {
                "events": [],
                "continuation_token": None
            }
        return response_content

    #--------------------------------------------------
    # Databases
    #--------------------------------------------------

    def get_installed_packages(self, database: str) -> Union[Dict, None]:
        use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)
        if use_graph_index:
            response = self.request(
                "get_model_package_versions",
                payload={"model_name": database},
            )
        else:
            response = self.request(
                "get_package_versions",
                path_params={"db_name": database},
            )
        if response.status_code == 404 and response.json().get("message", "") == "database not found":
            return None
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to retrieve package versions for {database}.", response
            )

        content = response.json()
        if not content:
            return None

        return safe_json_loads(content["package_versions"])

    def get_database(self, database: str):
        with debugging.span("get_database", dbname=database):
            if not database:
                raise ValueError("Database name must be provided to get database.")
            response = self.request(
                "get_db",
                path_params={},
                query_params={"name": database},
            )
            if response.status_code != 200:
                raise ResponseStatusException(f"Failed to get db. db:{database}", response)

            response_content = response.json()

            if (response_content.get("databases") and len(response_content["databases"]) == 1):
                db = response_content["databases"][0]
                return {
                    "id": db["id"],
                    "name": db["name"],
                    "created_by": db.get("created_by"),
                    "created_on": ms_to_timestamp(db.get("created_on")),
                    "deleted_by": db.get("deleted_by"),
                    "deleted_on": ms_to_timestamp(db.get("deleted_on")),
                    "state": db["state"],
                }
            else:
                return None

    def create_graph(self, name: str):
        with debugging.span("create_model", dbname=name):
            return self._create_database(name,"")

    def delete_graph(self, name:str, force=False, language: str = "rel"):
        prop_hdrs = debugging.gen_current_propagation_headers()
        if self.config.get("use_graph_index", USE_GRAPH_INDEX):
            keep_database = not force and self.config.get("reuse_model", True)
            with debugging.span("release_index", name=name, keep_database=keep_database, language=language):
                response = self.request(
                    "release_index",
                    payload={
                        "model_name": name,
                        "keep_database": keep_database,
                        "language": language,
                        "user_agent": get_pyrel_version(self.generation),
                    },
                    headers=prop_hdrs,
                )
                if (
                    response.status_code != 200
                    and not (
                        response.status_code == 404
                        and "database not found" in response.json().get("message", "")
                    )
                ):
                    raise ResponseStatusException(f"Failed to release index. Model: {name} ", response)
        else:
            with debugging.span("delete_model", name=name):
                self._delete_database(name, headers=prop_hdrs)

    def clone_graph(self, target_name:str, source_name:str, nowait_durable=True, force=False):
        if force and self.get_graph(target_name):
            self.delete_graph(target_name)
        with debugging.span("clone_model", target_name=target_name, source_name=source_name):
            return self._create_database(target_name,source_name)

    def _delete_database(self, name:str, headers:Dict={}):
        with debugging.span("_delete_database", dbname=name):
            response = self.request(
                "delete_db",
                path_params={"db_name": name},
                query_params={},
                headers=headers,
            )
            if response.status_code != 200:
                raise ResponseStatusException(f"Failed to delete db. db:{name} ", response)

    def _create_database(self, name:str, source_name:str):
        with debugging.span("_create_database", dbname=name):
            payload = {
                "name": name,
                "source_name": source_name,
            }
            response = self.request(
                "create_db", payload=payload, headers={}, query_params={},
            )
            if response.status_code != 200:
                raise ResponseStatusException(f"Failed to create db. db:{name}", response)

    #--------------------------------------------------
    # Engines
    #--------------------------------------------------

    def list_engines(
        self,
        state: str | None = None,
        name: str | None = None,
        type: str | None = None,
        size: str | None = None,
        created_by: str | None = None,
    ):
        response = self.request("list_engines")
        if response.status_code != 200:
            raise ResponseStatusException(
                "Failed to retrieve engines.", response
            )
        response_content = response.json()
        if not response_content:
            return []
        engines = [
            {
                "name": engine["name"],
                "id": engine["id"],
                "type": engine.get("type", "LOGIC"),
                "size": engine["size"],
                "state": engine["status"], # callers are expecting 'state'
                "created_by": engine["created_by"],
                "created_on": engine["created_on"],
                "updated_on": engine["updated_on"],
                # Optional fields (present in newer APIs / service-functions path)
                "auto_suspend_mins": engine.get("auto_suspend_mins"),
                "suspends_at": engine.get("suspends_at"),
                "settings": engine.get("settings"),
            }
            for engine in response_content.get("engines", [])
            if (state is None or engine.get("status") == state)
            and (name is None or name.upper() in engine.get("name", "").upper())
            and (type is None or engine.get("type", "LOGIC").upper() == type.upper())
            and (size is None or engine.get("size") == size)
            and (created_by is None or created_by.upper() in engine.get("created_by", "").upper())
        ]
        return sorted(engines, key=lambda x: x["name"])

    def get_engine(self, name: str, type: str):
        if type is None:
            raise Exception("Engine type is required. Valid types are: LOGIC, SOLVER, ML")
        engine_type_lower = type.lower()
        response = self.request("get_engine", path_params={"engine_name": name, "engine_type": engine_type_lower}, skip_auto_create=True)
        if response.status_code == 404: # engine not found return 404
            return None
        elif response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to retrieve engine {name}.", response
            )
        engine = response.json()
        if not engine:
            return None
        engine_state: EngineState = {
            "name": engine["name"],
            "id": engine["id"],
            "size": engine["size"],
            "type": engine.get("type", type),
            "state": engine["status"], # callers are expecting 'state'
            "created_by": engine["created_by"],
            "created_on": engine["created_on"],
            "updated_on": engine["updated_on"],
            "version": engine["version"],
            "auto_suspend": engine["auto_suspend_mins"],
            "suspends_at": engine["suspends_at"],
            "settings": engine.get("settings"),
        }
        return engine_state

    def _create_engine(
            self,
            name: str,
            type: str = "LOGIC",
            size: str | None = None,
            auto_suspend_mins: int | None = None,
            is_async: bool = False,
            headers: Dict[str, str] | None = None,
            settings: Dict[str, Any] | None = None,
        ):
        # only async engine creation supported via direct access
        if not is_async:
            return super()._create_engine(
                name,
                type=type,
                size=size,
                auto_suspend_mins=auto_suspend_mins,
                is_async=is_async,
                headers=headers,
                settings=settings,
            )
        engine_type_lower = type.lower()
        payload:Dict[str, Any] = {
            "name": name,
        }
        # Allow passing arbitrary engine settings (API-dependent).
        if settings:
            payload["settings"] = settings
        if auto_suspend_mins is not None:
            payload["auto_suspend_mins"] = auto_suspend_mins
        if size is None:
            size = self.config.get_default_engine_size()
        payload["size"] = size
        response = self.request(
            "create_engine",
            payload=payload,
            path_params={"engine_type": engine_type_lower},
            headers=headers,
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to create engine {name} with size {size}.", response
            )

    def delete_engine(self, name: str, type: str):
        response = self.request(
            "delete_engine",
            path_params={"engine_name": name, "engine_type": type.lower()},
            headers={},
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to delete engine {name}.", response
            )

    def suspend_engine(self, name: str, type: str | None = None):
        if type is None:
            type = "LOGIC"
        response = self.request(
            "suspend_engine",
            path_params={"engine_name": name, "engine_type": type.lower()},
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to suspend engine {name}.", response
            )

    def resume_engine_async(self, name: str, type: str | None = None, headers: Dict | None = None):
        if type is None:
            type = "LOGIC"
        response = self.request(
            "resume_engine",
            path_params={"engine_name": name, "engine_type": type.lower()},
            headers=headers or {},
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to resume engine {name}.", response
            )
        return {}

    def _poll_use_index(
        self,
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: str | None = None,
        program_span_id: str | None = None,
        headers: Dict | None = None,
    ):
        """Poll use_index to prepare indices for the given sources using DirectUseIndexPoller."""
        return DirectUseIndexPoller(
            self,
            app_name=app_name,
            sources=sources,
            model=model,
            engine_name=engine_name,
            engine_size=engine_size,
            language=self.language,
            program_span_id=program_span_id,
            headers=headers,
            generation=self.generation,
        ).poll()

    def maybe_poll_use_index(
        self,
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: str | None = None,
        program_span_id: str | None = None,
        headers: Dict | None = None,
    ):
        """Only call poll() if there are sources to process and cache is not valid."""
        sources_list = list(sources)
        self.database = model
        if sources_list:
            poller = DirectUseIndexPoller(
                self,
                app_name=app_name,
                sources=sources_list,
                model=model,
                engine_name=engine_name,
                engine_size=engine_size,
                language=self.language,
                program_span_id=program_span_id,
                headers=headers,
                generation=self.generation,
            )
            # If cache is valid (data freshness has not expired), skip polling
            if poller.cache.is_valid():
                cached_sources = len(poller.cache.sources)
                total_sources = len(sources_list)
                cached_timestamp = poller.cache._metadata.get("cachedIndices", {}).get(poller.cache.key, {}).get("last_use_index_update_on", "")

                message = f"Using cached data for {cached_sources}/{total_sources} data streams"
                if cached_timestamp:
                    print(f"\n{message} (cached at {cached_timestamp})\n")
                else:
                    print(f"\n{message}\n")
            else:
                return poller.poll()


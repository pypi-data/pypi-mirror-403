"""
Use Index Resources - Resources class with use_index functionality.
This class keeps the use_index retry logic in _exec and provides use_index methods.
"""
from __future__ import annotations
from typing import Iterable, Dict, Any

from .use_index_poller import UseIndexPoller
from ...config import Config
from ....tools.constants import Generation
from snowflake.snowpark import Session
from .error_handlers import ErrorHandler, UseIndexRetryErrorHandler

# Import Resources from snowflake - this creates a dependency but no circular import
# since snowflake.py doesn't import from this file
from .snowflake import Resources
from .util import (
    is_engine_issue as _is_engine_issue,
    is_database_issue as _is_database_issue,
    collect_error_messages,
)


class UseIndexResources(Resources):
    """
    Resources class with use_index functionality.
    Provides use_index polling methods and keeps use_index retry logic in _exec.
    """
    def __init__(
        self,
        profile: str | None = None,
        config: Config | None = None,
        connection: Session | None = None,
        dry_run: bool = False,
        reset_session: bool = False,
        generation: Generation | None = None,
        language: str = "rel",
    ):
        super().__init__(
            profile=profile,
            config=config,
            connection=connection,
            dry_run=dry_run,
            reset_session=reset_session,
            generation=generation,
        )
        self.database = ""
        self.language = language

    def _is_db_or_engine_error(self, e: Exception) -> bool:
        """Check if an exception indicates a database or engine error."""
        messages = collect_error_messages(e)
        for msg in messages:
            if msg and (_is_database_issue(msg) or _is_engine_issue(msg)):
                return True
        return False

    def _get_error_handlers(self) -> list[ErrorHandler]:
        # Ensure use_index retry happens before standard database/engine error handlers.
        return [UseIndexRetryErrorHandler(), *super()._get_error_handlers()]

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
        """Poll use_index to prepare indices for the given sources."""
        return UseIndexPoller(
            self,
            app_name,
            sources,
            model,
            engine_name,
            engine_size,
            self.language,
            program_span_id,
            headers,
            self.generation
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
            poller = UseIndexPoller(
                self,
                app_name,
                sources_list,
                model,
                engine_name,
                engine_size,
                self.language,
                program_span_id,
                headers,
                self.generation
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

    def _exec_with_gi_retry(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        inputs: Dict | None,
        readonly: bool,
        nowait_durable: bool,
        headers: Dict | None,
        bypass_index: bool,
        language: str,
        query_timeout_mins: int | None,
    ):
        """Execute with graph index retry logic.

        Attempts execution with gi_setup_skipped=True first. If an engine or database
        issue occurs, polls use_index and retries with gi_setup_skipped=False.
        """
        try:
            return self._exec_async_v2(
                database, engine, raw_code, inputs, readonly, nowait_durable,
                headers=headers, bypass_index=bypass_index, language=language,
                query_timeout_mins=query_timeout_mins, gi_setup_skipped=True,
            )
        except Exception as e:
            if not self._is_db_or_engine_error(e):
                raise e

            engine_name = engine or self.get_default_engine_name()
            engine_size = self.config.get_default_engine_size()
            self._poll_use_index(
                app_name=self.get_app_name(),
                sources=self.sources,
                model=database,
                engine_name=engine_name,
                engine_size=engine_size,
                headers=headers,
            )

            return self._exec_async_v2(
                database, engine, raw_code, inputs, readonly, nowait_durable,
                headers=headers, bypass_index=bypass_index, language=language,
                query_timeout_mins=query_timeout_mins, gi_setup_skipped=False,
            )

    def _execute_code(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        inputs: Dict | None,
        readonly: bool,
        nowait_durable: bool,
        headers: Dict | None,
        bypass_index: bool,
        language: str,
        query_timeout_mins: int | None,
    ) -> Any:
        """Override to use retry logic with use_index polling."""
        return self._exec_with_gi_retry(
            database, engine, raw_code, inputs, readonly, nowait_durable,
            headers, bypass_index, language, query_timeout_mins
        )

from __future__ import annotations

import json
from typing import Any, Dict, List, Protocol, Tuple

from .... import debugging
from ....errors import EngineProvisioningFailed
from ...config import Config
from ...types import EngineState
from ...util import poll_with_specified_overhead

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Keep the same placeholder string as `snowflake.py` so `Resources._exec_sql()` will
# replace it with the actual app name.
APP_NAME = "___RAI_APP___"
ENGINE_SCHEMA = "experimental"
API_SCHEMA = f"{APP_NAME}.{ENGINE_SCHEMA}"

# Cloud-specific engine sizes
INTERNAL_ENGINE_SIZES = ["XS", "S", "M", "L"]
ENGINE_SIZES_AWS = ["HIGHMEM_X64_S", "HIGHMEM_X64_M", "HIGHMEM_X64_L"]
ENGINE_SIZES_AZURE = ["HIGHMEM_X64_S", "HIGHMEM_X64_M", "HIGHMEM_X64_SL"]

# ---------------------------------------------------------------------------
# Engine types
# ---------------------------------------------------------------------------

class EngineType:
    """Engine type constants with descriptions."""

    LOGIC = "LOGIC"
    SOLVER = "SOLVER"
    ML = "ML"

    _LABELS = {
        LOGIC: "Logic",
        SOLVER: "Prescriptive",
        ML: "Predictive",
    }

    _DESCRIPTIONS = {
        LOGIC: "Logic engine for deductive reasoning and relational queries",
        SOLVER: "Optimization engine using mathematical solvers for prescriptive reasoning",
        ML: "Machine learning engine for pattern recognition and predictive reasoning",
    }

    @classmethod
    def get_label(cls, type: str) -> str:
        """Get the user-friendly label for an engine type."""
        return cls._LABELS.get(type, type)

    @classmethod
    def get_label_with_value(cls, type: str) -> str:
        """Get the user-friendly label with the value in parentheses."""
        label = cls.get_label(type)
        return f"{label} ({type})"

    @classmethod
    def get_description(cls, type: str) -> str:
        """Get the description for an engine type."""
        return cls._DESCRIPTIONS.get(type, "Unknown engine type")

    @classmethod
    def is_valid(cls, type: str) -> bool:
        """Check if an engine type is valid."""
        return type in cls._DESCRIPTIONS

    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all valid engine types."""
        return list(cls._DESCRIPTIONS.keys())


class _ExecResources(Protocol):
    """Minimal surface EngineServiceSQL needs from Resources (composition, no mixins)."""

    config: Config

    def _exec(
        self,
        code: str,
        params: Any | None = None,
        raw: bool = False,
        help: bool = True,
        skip_engine_db_error_retry: bool = False,
    ) -> Any:
        """Execute a statement via the owning resources object."""
        ...

    def get_cloud_provider(self) -> str:
        """Return the configured cloud provider identifier (e.g. 'aws', 'azure')."""
        ...


# ---------------------------------------------------------------------------
# Engine Service
# ---------------------------------------------------------------------------
class EngineServiceSQL:
    """Snowflake engine management backed by SQL stored procedures."""

    def __init__(self, resources: _ExecResources):
        """Create an engine service bound to a resources-like executor."""
        self._res = resources

    @staticmethod
    def _parse_settings(val: Any) -> Dict[str, Any] | None:
        if val is None:
            return None
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return None
            try:
                parsed = json.loads(s)
                return parsed if isinstance(parsed, dict) else {"value": parsed}
            except Exception:
                return {"value": val}
        # Snowflake VARIANT may arrive as a list/tuple/etc; preserve it under a wrapper
        return {"value": val}

    def list_engines(
        self,
        *,
        state: str | None = None,
        name: str | None = None,
        type: str | None = None,
        size: str | None = None,
        created_by: str | None = None,
    ) -> List[Dict[str, Any]]:
        """
        List engines with optional filtering.

        Uses parameterized queries (? placeholders) for SQL injection protection.
        """

        where_conditions: list[str] = []
        params: list[Any] = []

        if state:
            where_conditions.append("STATUS = ?")
            params.append(state.upper())
        if name:
            where_conditions.append("UPPER(NAME) LIKE ?")
            params.append(f"%{name.upper()}%")
        if type:
            where_conditions.append("TYPE = ?")
            params.append(type.upper())
        if size:
            where_conditions.append("SIZE = ?")
            params.append(size)
        if created_by:
            where_conditions.append("UPPER(CREATED_BY) LIKE ?")
            params.append(f"%{created_by.upper()}%")

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        where_suffix = f" {where_clause}" if where_clause else ""
        statement = f"""
            SELECT
                NAME, TYPE, ID, SIZE, STATUS, CREATED_BY, CREATED_ON, UPDATED_ON,
                AUTO_SUSPEND_MINS, SUSPENDS_AT, SETTINGS
            FROM {API_SCHEMA}.engines{where_suffix}
            ORDER BY NAME ASC;
        """

        results = self._res._exec(statement, params)
        if not results:
            return []

        return [
            {
                "name": row["NAME"],
                "type": row["TYPE"],
                "id": row["ID"],
                "size": row["SIZE"],
                "state": row["STATUS"],  # callers expect 'state'
                "created_by": row["CREATED_BY"],
                "created_on": row["CREATED_ON"],
                "updated_on": row["UPDATED_ON"],
                "auto_suspend_mins": row["AUTO_SUSPEND_MINS"],
                "suspends_at": row["SUSPENDS_AT"],
                "settings": self._parse_settings(
                    # Snowpark Row supports dict-style indexing but not `.get()`.
                    row["SETTINGS"] if "SETTINGS" in row else None
                ),
            }
            for row in results
        ]

    def get_engine(self, name: str, type: str) -> EngineState | None:
        """Fetch a single engine by (name, type), returning None if not found."""
        results = self._res._exec(
            f"""
            SELECT
                NAME, TYPE, ID, SIZE, STATUS, CREATED_BY, CREATED_ON, UPDATED_ON,
                VERSION, AUTO_SUSPEND_MINS, SUSPENDS_AT, SETTINGS
            FROM {API_SCHEMA}.engines
            WHERE NAME = ? AND TYPE = ?;
            """,
            [name, type],
        )
        if not results:
            return None
        engine = results[0]
        if not engine:
            return None
        engine_state: EngineState = {
            "name": engine["NAME"],
            "type": engine["TYPE"],
            "id": engine["ID"],
            "size": engine["SIZE"],
            "state": engine["STATUS"],  # callers expect 'state'
            "created_by": engine["CREATED_BY"],
            "created_on": engine["CREATED_ON"],
            "updated_on": engine["UPDATED_ON"],
            "version": engine["VERSION"],
            "auto_suspend": engine["AUTO_SUSPEND_MINS"],
            "suspends_at": engine["SUSPENDS_AT"],
            "settings": self._parse_settings(engine["SETTINGS"] if "SETTINGS" in engine else None),
        }
        return engine_state

    def _create_engine(
        self,
        *,
        name: str,
        type: str = EngineType.LOGIC,
        size: str | None = None,
        auto_suspend_mins: int | None = None,
        is_async: bool = False,
        headers: Dict | None = None,
        settings: Dict[str, Any] | None = None,
    ) -> None:
        """Create an engine using the appropriate stored procedure.

        Note: `headers` is accepted for API compatibility; it is not currently used
        in the Snowflake implementation.
        """
        API = "create_engine_async" if is_async else "create_engine"
        if size is None:
            size = self._res.config.get_default_engine_size()
        if auto_suspend_mins is None:
            auto_suspend_mins = self._res.config.get_default_auto_suspend_mins()

        try:
            with debugging.span(API, name=name, size=size, auto_suspend_mins=auto_suspend_mins, engine_type=type):
                payload: Dict[str, Any] | None = None
                if settings:
                    payload = {"settings": dict(settings)}
                if auto_suspend_mins is not None:
                    payload = dict(payload or {})
                    payload["auto_suspend_mins"] = auto_suspend_mins

                if payload is None:
                    self._res._exec(
                        f"call {API_SCHEMA}.{API}(?, ?, ?, null);",
                        [type, name, size],
                    )
                else:
                    self._res._exec(
                        f"call {API_SCHEMA}.{API}(?, ?, ?, PARSE_JSON(?));",
                        [type, name, size, json.dumps(payload)],
                    )
        except Exception as e:
            raise EngineProvisioningFailed(name, e) from e

    def create_engine(
        self,
        name: str,
        type: str | None = None,
        size: str | None = None,
        auto_suspend_mins: int | None = None,
        headers: Dict | None = None,
        settings: Dict[str, Any] | None = None,
    ) -> None:
        """Create an engine (synchronous variant)."""
        if type is None:
            type = EngineType.LOGIC
        self._create_engine(
            name=name,
            type=type,
            size=size,
            auto_suspend_mins=auto_suspend_mins,
            headers=headers,
            settings=settings,
        )

    def create_engine_async(
        self,
        name: str,
        type: str = EngineType.LOGIC,
        size: str | None = None,
        auto_suspend_mins: int | None = None,
    ) -> None:
        """Create an engine asynchronously."""
        self._create_engine(
            name=name,
            type=type,
            size=size,
            auto_suspend_mins=auto_suspend_mins,
            is_async=True,
        )

    def delete_engine(self, name: str, type: str) -> None:
        """Delete an engine by (name, type)."""
        self._res._exec(
            f"call {API_SCHEMA}.delete_engine(?, ?);",
            [type, name],
        )

    def suspend_engine(self, name: str, type: str | None = None) -> None:
        """Suspend an engine by name (and optional type)."""
        if type is None:
            type = EngineType.LOGIC
        self._res._exec(
            f"call {API_SCHEMA}.suspend_engine(?, ?);",
            [type, name],
        )

    def resume_engine(self, name: str, type: str | None = None, headers: Dict | None = None) -> Dict[str, Any]:
        """Resume an engine and block until it is READY.

        This preserves historical behavior where `resume_engine` was synchronous.
        Use `resume_engine_async` for a fire-and-forget resume call.
        """
        if type is None:
            type = EngineType.LOGIC
        self.resume_engine_async(name, type=type, headers=headers)
        poll_with_specified_overhead(
            lambda: (self.get_engine(name, type) or {}).get("state") == "READY",
            overhead_rate=0.1,
            max_delay=0.5,
            timeout=900,
        )
        return {}

    def resume_engine_async(self, name: str, type: str | None = None, headers: Dict | None = None) -> Dict[str, Any]:
        """Resume an engine asynchronously and return an API-compatible payload.

        Note: `headers` is accepted for API compatibility; it is not currently used
        in the Snowflake implementation.
        """
        if type is None:
            type = EngineType.LOGIC
        self._res._exec(
            f"call {API_SCHEMA}.resume_engine_async(?, ?);",
            [type, name],
        )
        return {}

    def validate_engine_size(self, size: str) -> Tuple[bool, List[str]]:
        """Validate an engine size, returning (is_valid, allowed_sizes_if_invalid)."""
        if size is not None:
            sizes = self.get_engine_sizes()
            if size not in sizes:
                return False, sizes
        return True, []

    def get_engine_sizes(self, cloud_provider: str | None = None) -> List[str]:
        """Return the list of valid engine sizes for the given cloud provider."""
        if cloud_provider is None:
            cloud_provider = self._res.get_cloud_provider()

        if cloud_provider == "azure":
            sizes = ENGINE_SIZES_AZURE
        else:
            sizes = ENGINE_SIZES_AWS

        if self._res.config.show_all_engine_sizes():
            return INTERNAL_ENGINE_SIZES + sizes
        return sizes

    def alter_engine_pool(self, size: str | None = None, mins: int | None = None, maxs: int | None = None) -> None:
        """Alter engine pool node limits for Snowflake."""
        # Keep the exact SQL shape used by Resources for backwards compatibility.
        self._res._exec(f"call {APP_NAME}.api.alter_engine_pool_node_limits('{size}', {mins}, {maxs});")


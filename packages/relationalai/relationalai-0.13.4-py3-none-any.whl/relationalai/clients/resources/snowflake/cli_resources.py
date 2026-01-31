"""
CLI Resources - Resources class for CLI operations.
Re-raises exceptions without transformation and provides CLI utility methods.
"""
from __future__ import annotations
import json
from typing import Any

from ....tools.constants import RAI_APP_NAME

# Import Resources from snowflake - this creates a dependency but no circular import
# since snowflake.py doesn't import from this file
from .snowflake import Resources, ExecContext
from .error_handlers import AppMissingErrorHandler, AppFunctionMissingErrorHandler, ServiceNotStartedErrorHandler


class CLIResources(Resources):
    """
    Resources class for CLI operations.
    Re-raises exceptions without transformation and provides CLI utility methods.
    """

    def _handle_standard_exec_errors(self, e: Exception, ctx: ExecContext) -> Any | None:
        """
        For CLI resources, keep exceptions raw except for few specific cases.
        """
        message = str(e).lower()
        for handler in (
            ServiceNotStartedErrorHandler(),
            AppMissingErrorHandler(),
            AppFunctionMissingErrorHandler(),
        ):
            if handler.matches(e, message, ctx, self):
                handler.handle(e, ctx, self)
        raise e

    def list_warehouses(self):
        """List all warehouses in the Snowflake account."""
        results = self._exec("SHOW WAREHOUSES")
        if not results:
            return []
        return [{"name": name}
                for (name, *rest) in results]

    def list_compute_pools(self):
        """List all compute pools in the Snowflake account."""
        results = self._exec("SHOW COMPUTE POOLS")
        if not results:
            return []
        return [{"name": name, "status": status, "min_nodes": min_nodes, "max_nodes": max_nodes, "instance_family": instance_family}
                for (name, status, min_nodes, max_nodes, instance_family, *rest) in results]

    def list_roles(self):
        """List all available roles in the Snowflake account."""
        results = self._exec("SELECT CURRENT_AVAILABLE_ROLES()")
        if not results:
            return []
        # the response is a single row with a single column containing
        # a stringified JSON array of role names:
        row = results[0]
        if not row:
            return []
        return [{"name": name} for name in json.loads(row[0])]

    def list_apps(self):
        """List all applications in the Snowflake account."""
        all_apps = self._exec(f"SHOW APPLICATIONS LIKE '{RAI_APP_NAME}'")
        if not all_apps:
            all_apps = self._exec("SHOW APPLICATIONS")
            if not all_apps:
                return []
        return [{"name": name}
                for (time, name, *rest) in all_apps]

    def list_databases(self):
        """List all databases in the Snowflake account."""
        results = self._exec("SHOW DATABASES")
        if not results:
            return []
        return [{"name": name}
                for (time, name, *rest) in results]

    def list_sf_schemas(self, database: str):
        """List all schemas in a given database."""
        results = self._exec(f"SHOW SCHEMAS IN {database}")
        if not results:
            return []
        return [{"name": name}
                for (time, name, *rest) in results]

    def list_tables(self, database: str, schema: str):
        """List all tables and views in a given schema."""
        results = self._exec(f"SHOW OBJECTS IN {database}.{schema}")
        items = []
        if results:
            for (time, name, db_name, schema_name, kind, *rest) in results:
                items.append({"name": name, "kind": kind.lower()})
        return items

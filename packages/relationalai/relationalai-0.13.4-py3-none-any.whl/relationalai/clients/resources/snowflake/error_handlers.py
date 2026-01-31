"""
Error handlers for Snowflake Resources using Strategy Pattern.

Each error handler encapsulates the detection logic and exception creation
for a specific type of error. Handlers are processed in order until one matches.
"""
from __future__ import annotations
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ....errors import (
    DuoSecurityFailed,
    EngineNotFoundException,
    EnginePending,
    EngineNameValidationException,
    EngineProvisioningFailed,
    EngineResumeFailed,
    RAIAbortedTransactionError,
    RAIException,
    SnowflakeAppMissingException,
    SnowflakeDatabaseException,
    SnowflakeRaiAppNotStarted,
)

if TYPE_CHECKING:
    from .snowflake import ExecContext
    from .snowflake import Resources

from .util import is_database_issue, is_engine_issue, collect_error_messages

class ErrorHandler(ABC):
    """Base class for error handlers using Strategy Pattern."""

    @abstractmethod
    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        """Check if this handler can process the error."""
        pass

    @abstractmethod
    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        """Handle the error and either raise an exception or return an alternate result."""
        pass


class DuoSecurityErrorHandler(ErrorHandler):
    """Handle Duo security authentication errors."""

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        messages = collect_error_messages(error)
        return any("duo security" in msg for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        raise DuoSecurityFailed(error)


class AppMissingErrorHandler(ErrorHandler):
    """Handle missing RAI app database errors."""

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        rai_app = resources.config.get("rai_app_name", "")
        if not isinstance(rai_app, str):
            return False
        pattern = f"database '{rai_app}' does not exist or not authorized."
        messages = collect_error_messages(error)
        return any(re.search(pattern.lower(), msg) for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        rai_app = resources.config.get("rai_app_name", "")
        assert isinstance(rai_app, str), f"rai_app_name must be a string, not {type(rai_app)}"
        raise SnowflakeAppMissingException(rai_app, resources.config.get("role"))


class AppFunctionMissingErrorHandler(ErrorHandler):
    """Handle missing RAI app when app-scoped UDFs are unknown.

    When the RelationalAI Snowflake native application isn't installed (or is installed
    under a different name / not authorized), Snowflake can surface errors like:

        SQL compilation error: Unknown user-defined function <APP>.<SCHEMA>.<FUNC>.

    This should be presented to users as an "app missing" configuration issue, not
    as a raw SQL error.
    """

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        rai_app = resources.config.get("rai_app_name", "")
        if not isinstance(rai_app, str) or not rai_app:
            return False

        rai_app_lower = rai_app.lower()
        # Normalize whitespace/newlines because Snowpark error strings may wrap.
        messages = [" ".join(msg.split()).lower() for msg in collect_error_messages(error)]

        # Examples:
        # - "unknown user-defined function sqlib_ia_na_app.experimental.resume_engine_async."
        # - "unknown user-defined function sqlib_ia_na_app.api.alter_engine_pool_node_limits."
        needle = f"unknown user-defined function {rai_app_lower}."
        return any(needle in msg for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        rai_app = resources.config.get("rai_app_name", "")
        assert isinstance(rai_app, str), f"rai_app_name must be a string, not {type(rai_app)}"
        raise SnowflakeAppMissingException(rai_app, resources.config.get("role"))


class DatabaseErrorsHandler(ErrorHandler):
    """Handle database-related errors from Snowflake/RAI."""

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        """Check if error is database-related."""
        # Use collect_error_messages to get all messages from exception chain
        messages = collect_error_messages(error)
        return any(is_database_issue(msg) for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        """Handle database errors and raise appropriate exception."""
        raise SnowflakeDatabaseException(error)


class EngineErrorsHandler(ErrorHandler):
    """Handle all engine-related errors from Snowflake/RAI."""

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        """Check if error is engine-related."""
        # Use collect_error_messages to get all messages from exception chain
        messages = collect_error_messages(error)
        return any(is_engine_issue(msg) for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        """Handle engine errors and raise appropriate exception."""
        # Use collect_error_messages to get all messages from exception chain
        messages = collect_error_messages(error)
        engine = resources.get_default_engine_name()
        assert isinstance(engine, str), f"engine must be a string, not {type(engine)}"

        # Check all collected messages for engine error patterns
        for message in messages:
            if "engine is in pending" in message or "engine is provisioning" in message:
                raise EnginePending(engine)
            elif "engine not found" in message or "no engines found" in message:
                raise EngineNotFoundException(engine, str(error))
            elif "engine was deleted" in message:
                raise EngineNotFoundException(engine, "Engine was deleted")
            elif "engine is suspended" in message:
                raise EngineResumeFailed(engine)
            elif "create/resume" in message:
                raise EngineProvisioningFailed(engine, error)

        # Generic engine error - use the original error message
        raise RAIException(str(error))


class ServiceNotStartedErrorHandler(ErrorHandler):
    """Handle RAI service not started errors."""

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        messages = [" ".join(msg.split()).lower() for msg in collect_error_messages(error)]
        return any(
            (
                # Native app not activated / service not started
                "service has not been started" in msg
                # Native app suspended/deactivated; SPCS control plane is unreachable
                or "not reachable: service suspended" in msg
            )
            for msg in messages
        )

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        rai_app = resources.config.get("rai_app_name", "")
        assert isinstance(rai_app, str), f"rai_app_name must be a string, not {type(rai_app)}"
        raise SnowflakeRaiAppNotStarted(rai_app)


class TransactionAbortedErrorHandler(ErrorHandler):
    """Handle transaction aborted errors with problem details."""

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        messages = collect_error_messages(error)
        return any(re.search(r"state:\s*aborted", msg) for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        # Use collect_error_messages to get all messages from exception chain
        messages = collect_error_messages(error)
        # Check all collected messages for transaction ID
        for message in messages:
            txn_id_match = re.search(r"id:\s*([0-9a-f\-]+)", message)
            if txn_id_match:
                problems = resources.get_transaction_problems(txn_id_match.group(1))
                if problems:
                    # Extract problem details (handle both dict and object formats)
                    for problem in problems:
                        if isinstance(problem, dict):
                            type_field = problem.get('TYPE')
                            message_field = problem.get('MESSAGE')
                            report_field = problem.get('REPORT')
                        else:
                            type_field = problem.TYPE
                            message_field = problem.MESSAGE
                            report_field = problem.REPORT
                        raise RAIAbortedTransactionError(type_field, message_field, report_field)
        raise RAIException(str(error))


class UseIndexRetryErrorHandler(ErrorHandler):
    """Handle engine/database errors by polling use_index and retrying the execution.

    Intended for UseIndexResources and subclasses. Register this handler *before*
    the standard Database/Engine error handlers.
    """

    def matches(self, error: Exception, message: str, ctx: 'ExecContext', resources: 'Resources') -> bool:
        if ctx.skip_engine_db_error_retry:
            return False
        messages = collect_error_messages(error)
        return any(msg and (is_database_issue(msg) or is_engine_issue(msg)) for msg in messages)

    def handle(self, error: Exception, ctx: 'ExecContext', resources: 'Resources') -> Any | None:
        poll_use_index = getattr(resources, "_poll_use_index", None)
        if not callable(poll_use_index):
            return None

        engine = resources.get_default_engine_name()
        engine_size = resources.config.get_default_engine_size()
        assert isinstance(engine, str), f"engine must be a string, not {type(engine)}"

        model = getattr(resources, "database", "")
        try:
            poll_use_index(
                app_name=resources.get_app_name(),
                sources=resources.sources,
                model=model,
                engine_name=engine,
                engine_size=engine_size,
            )
        except EngineNameValidationException as e:
            raise EngineNameValidationException(engine) from e

        return ctx.re_execute(resources)


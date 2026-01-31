"""
Engine state handlers for auto_create_engine methods using Strategy Pattern.

Each state handler encapsulates the logic for handling a specific engine state
(PENDING, SUSPENDED, READY, GONE, or None/missing). Handlers are separated
for sync and async modes since they have different behaviors.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Any, cast, Union

from ....errors import EngineNotFoundException, EngineProvisioningFailed, EngineResumeFailed, EngineSizeMismatchWarning
from ....tools.cli_controls import Spinner
from ...util import poll_with_specified_overhead

if TYPE_CHECKING:
    from .snowflake import Resources
    from ...types import EngineState
    EngineDict = Union[EngineState, Dict[str, Any]]
else:
    EngineDict = Dict[str, Any]


@dataclass
class EngineContext:
    """Context for engine state handling."""
    name: str
    size: str | None
    type: str
    headers: Dict | None
    requested_size: str | None  # Size explicitly requested by user
    spinner: Spinner | None = None  # For async mode UI updates
    span: Any = None  # For sync mode debugging span


class EngineStateHandler(ABC):
    """Base class for engine state handlers using Strategy Pattern."""

    @abstractmethod
    def handles_state(self, state: str | None) -> bool:
        """Check if this handler can process the given engine state."""
        pass

    @abstractmethod
    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        """
        Handle the engine state and return updated engine dict or None.

        Returns:
            - Updated engine dict if engine should remain
            - None if engine should be deleted/recreated
        """
        pass


# ============================================================================
# Sync Mode Handlers
# ============================================================================

class SyncPendingStateHandler(EngineStateHandler):
    """Handle PENDING state in sync mode - poll until ready."""

    def handles_state(self, state: str | None) -> bool:
        return state == "PENDING"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        # Warn if requested size doesn't match pending engine size
        if context.requested_size is not None and engine.get("size") != context.requested_size:
            existing_size = engine.get("size") or ""
            EngineSizeMismatchWarning(context.name, existing_size, context.requested_size)

        # Poll until engine is ready
        with Spinner(
            "Waiting for engine to be initialized",
            "Engine ready",
        ):
            poll_with_specified_overhead(
                lambda: resources.is_engine_ready(context.name, context.type),
                overhead_rate=0.1,
                max_delay=0.5,
                timeout=900
            )

        # Return updated engine (should be READY now)
        updated_engine = resources.get_engine(context.name, context.type)
        return cast(EngineDict, updated_engine) if updated_engine else None


class SyncSuspendedStateHandler(EngineStateHandler):
    """Handle SUSPENDED state in sync mode - resume and poll until ready."""

    def handles_state(self, state: str | None) -> bool:
        return state == "SUSPENDED"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        with Spinner(
            f"Resuming engine '{context.name}'",
            f"Engine '{context.name}' resumed",
            f"Failed to resume engine '{context.name}'"
        ):
            try:
                resources.resume_engine_async(context.name, type=context.type, headers=context.headers)
                poll_with_specified_overhead(
                    lambda: resources.is_engine_ready(context.name, context.type),
                    overhead_rate=0.1,
                    max_delay=0.5,
                    timeout=900
                )
            except Exception:
                raise EngineResumeFailed(context.name)

        # Return updated engine (should be READY now)
        updated_engine = resources.get_engine(context.name, context.type)
        return cast(EngineDict, updated_engine) if updated_engine else None


class SyncReadyStateHandler(EngineStateHandler):
    """Handle READY state in sync mode - set active and return."""

    def handles_state(self, state: str | None) -> bool:
        return state == "READY"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        # Warn if requested size doesn't match ready engine size
        if context.requested_size is not None and engine.get("size") != context.requested_size:
            existing_size = engine.get("size") or ""
            EngineSizeMismatchWarning(context.name, existing_size, context.requested_size)

        # Cast to EngineState for _set_active_engine
        if TYPE_CHECKING:
            from ...types import EngineState
            resources._set_active_engine(cast(EngineState, engine))
        else:
            resources._set_active_engine(engine)  # type: ignore[arg-type]
        return engine


class SyncGoneStateHandler(EngineStateHandler):
    """Handle GONE state in sync mode - delete and return None to trigger recreation."""

    def handles_state(self, state: str | None) -> bool:
        return state == "GONE"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        try:
            # "Gone" is abnormal condition when metadata and SF service don't match
            # Therefore, we have to delete the engine and create a new one
            # It could be case that engine is already deleted, so we have to catch the exception
            resources.delete_engine(context.name, context.type)
            # After deleting the engine, return None so that we can create a new engine
            return None
        except Exception as e:
            # If engine is already deleted, we will get an exception
            # We can ignore this exception and create a new engine
            if isinstance(e, EngineNotFoundException):
                return None
            else:
                raise EngineProvisioningFailed(context.name, e) from e


class SyncMissingEngineHandler(EngineStateHandler):
    """Handle missing engine (None) in sync mode - create synchronously."""

    def handles_state(self, state: str | None) -> bool:
        return state is None

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        # This handler is called when engine doesn't exist
        # Create engine synchronously with spinner
        with Spinner(
            f"Auto-creating engine {context.name}",
            f"Auto-created engine {context.name}",
            "Engine creation failed",
        ):
            resources.create_engine(
                context.name,
                size=context.size,
                type=context.type,
                headers=context.headers,
            )

        return resources.get_engine(context.name, context.type)


# ============================================================================
# Async Mode Handlers
# ============================================================================

class AsyncPendingStateHandler(EngineStateHandler):
    """Handle PENDING state in async mode - just update spinner, don't poll."""

    def handles_state(self, state: str | None) -> bool:
        return state == "PENDING"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        # In async mode, just update spinner - use_index will wait for engine to be ready
        if context.spinner:
            context.spinner.update_messages({
                "finished_message": f"Starting engine {context.name}",
            })

        return engine


class AsyncSuspendedStateHandler(EngineStateHandler):
    """Handle SUSPENDED state in async mode - resume asynchronously."""

    def handles_state(self, state: str | None) -> bool:
        return state == "SUSPENDED"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        if context.spinner:
            context.spinner.update_messages({
                "finished_message": f"Resuming engine {context.name}",
            })

        try:
            resources.resume_engine_async(context.name, type=context.type)
        except Exception:
            raise EngineResumeFailed(context.name)

        return engine


class AsyncReadyStateHandler(EngineStateHandler):
    """Handle READY state in async mode - set active."""

    def handles_state(self, state: str | None) -> bool:
        return state == "READY"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        if context.spinner:
            context.spinner.update_messages({
                "finished_message": f"Engine {context.name} initialized",
            })

        # Cast to EngineState for _set_active_engine
        if TYPE_CHECKING:
            from ...types import EngineState
            resources._set_active_engine(cast(EngineState, engine))
        else:
            resources._set_active_engine(engine)  # type: ignore[arg-type]
        return engine


class AsyncGoneStateHandler(EngineStateHandler):
    """Handle GONE state in async mode - delete and return None to trigger recreation."""

    def handles_state(self, state: str | None) -> bool:
        return state == "GONE"

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        if not engine:
            return None

        if context.spinner:
            context.spinner.update_messages({
                "message": f"Restarting engine {context.name}",
            })

        try:
            # "Gone" is abnormal condition when metadata and SF service don't match
            # Therefore, we have to delete the engine and create a new one
            # It could be case that engine is already deleted, so we have to catch the exception
            # Set it to None so that we can create a new engine asynchronously
            resources.delete_engine(context.name, context.type)
            return None
        except Exception as e:
            # If engine is already deleted, we will get an exception
            # We can ignore this exception and create a new engine asynchronously
            if isinstance(e, EngineNotFoundException):
                return None
            else:
                raise EngineProvisioningFailed(context.name, e) from e


class AsyncMissingEngineHandler(EngineStateHandler):
    """Handle missing engine (None) in async mode - create asynchronously."""

    def handles_state(self, state: str | None) -> bool:
        return state is None

    def handle(self, engine: EngineDict | None, context: EngineContext, resources: 'Resources') -> EngineDict | None:
        # This handler is called when engine doesn't exist
        # Create engine asynchronously
        resources.create_engine_async(context.name, size=context.size, type=context.type)

        if context.spinner:
            context.spinner.update_messages({
                "finished_message": f"Starting engine {context.name}...",
            })
        return None  # Engine is being created asynchronously


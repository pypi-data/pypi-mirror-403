"""Runtime context for accessing the current Runtime instance.

This module provides utilities for accessing the current Runtime instance
from anywhere in your application after runtime.start() or runtime.serve().

Example - Direct access:
    >>> from amirpc import Runtime
    >>> from amirpc.context import get_runtime
    >>>
    >>> runtime = Runtime.from_env()
    >>> await runtime.start()
    >>>
    >>> # Anywhere in your app (handlers, scheduled tasks, etc.)
    >>> rt = get_runtime()
    >>> client = rt.client(MyClient)

Example - Dependency injection in callbacks:
    >>> from amirpc import Runtime, RuntimeDep
    >>>
    >>> async def on_startup(runtime: RuntimeDep):
    ...     client = runtime.client(OrchestratorClient)
    ...     await client.workers.register(worker_id)
    >>>
    >>> runtime = Runtime.from_env()
    >>> runtime.serve([MyServer], on_startup=on_startup)
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Annotated

from fast_depends import Depends

if TYPE_CHECKING:
    from amirpc import Runtime

# Context variable for storing runtime in async context
_runtime_var: ContextVar[Runtime | None] = ContextVar("runtime", default=None)


def get_runtime() -> Runtime:
    """Get the current Runtime instance.

    Works anywhere after runtime.start() or during runtime.serve():
    - In RPC handlers
    - In scheduled tasks
    - In on_startup/on_shutdown callbacks
    - In any async code running within the runtime context

    Returns:
        The current Runtime instance.

    Raises:
        RuntimeError: If no runtime is active (before start() or after stop()).
    """
    runtime = _runtime_var.get()
    if runtime is None:
        raise RuntimeError(
            "No runtime in context. Ensure runtime.start() was called "
            "or you are within runtime.serve()."
        )
    return runtime


def set_runtime(runtime: Runtime | None) -> None:
    """Set the current Runtime instance.

    This is called internally by Runtime before invoking lifecycle callbacks.

    Args:
        runtime: The Runtime instance, or None to clear.
    """
    _runtime_var.set(runtime)


# Type alias for dependency injection
RuntimeDep = Annotated["Runtime", Depends(get_runtime)]
"""Type alias for injecting Runtime in lifecycle callbacks.

Example:
    >>> async def on_startup(runtime: RuntimeDep):
    ...     client = runtime.client(MyClient)
    ...     await client.do_something()
"""

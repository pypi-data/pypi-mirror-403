"""Context utilities for amirpc."""

from amirpc.context.runtime import RuntimeDep, get_runtime, set_runtime
from amirpc.context.user import (
    USER_CONTEXT_HEADER,
    CurrentUser,
    UserContext,
    deserialize_user_context,
    get_user_context,
    serialize_user_context,
    set_user_context,
)

__all__ = [
    "USER_CONTEXT_HEADER",
    "CurrentUser",
    "RuntimeDep",
    "UserContext",
    "deserialize_user_context",
    "get_runtime",
    "get_user_context",
    "serialize_user_context",
    "set_runtime",
    "set_user_context",
]

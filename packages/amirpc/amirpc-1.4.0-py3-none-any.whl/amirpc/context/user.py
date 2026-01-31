"""User context propagation through NATS headers.

This module provides utilities for passing authenticated user context
from gateway to services via NATS message headers.
"""

import base64
import json
from contextvars import ContextVar
from logging import getLogger
from typing import Annotated

from fast_depends import Depends
from pydantic import BaseModel, Field

logger = getLogger(__name__)

# Header name for user context in NATS messages
USER_CONTEXT_HEADER = "X-AMI-User-Context"

# Context variable for storing user context in async tasks
_user_context_var: ContextVar["UserContext | None"] = ContextVar(
    "user_context", default=None
)


class UserContext(BaseModel):
    """User context propagated from gateway to services.

    This model contains authenticated user information extracted from
    Keycloak JWT token and passed through NATS headers.
    """

    id: str = Field(..., description="User ID (Keycloak sub)")
    email: str | None = Field(None, description="User email address")
    username: str | None = Field(None, description="Username (preferred_username)")
    roles: list[str] = Field(default_factory=list, description="Realm roles")
    permissions: list[str] = Field(
        default_factory=list, description="Client roles (permissions)"
    )
    organization_name: str | None = Field(None, description="User organization name")
    organization_id: str | None = Field(None, description="User organization ID")

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission (supports wildcards).

        Args:
            permission: Permission pattern to check (e.g., "orchestrator:workers:view")

        Returns:
            True if user has permission

        Examples:
            >>> user.has_permission("orchestrator:workers:view")
            True
            >>> user.has_permission("orchestrator:*")
            True
        """
        if "*" in self.permissions:
            return True

        for perm in self.permissions:
            if _match_permission_pattern(permission, perm):
                return True

        return False

    def has_role(self, role: str) -> bool:
        """Check if user has specific realm role.

        Args:
            role: Role name to check

        Returns:
            True if user has role
        """
        return role in self.roles


def _match_permission_pattern(permission: str, pattern: str) -> bool:
    """Check if permission matches pattern with wildcard support.

    Args:
        permission: Permission to check (e.g., "orchestrator:workers:view")
        pattern: Pattern to match against (e.g., "orchestrator:*")

    Returns:
        True if permission matches pattern
    """
    if pattern == "*":
        return True

    if "*" not in pattern:
        return permission == pattern

    # Split by colon and match parts
    perm_parts = permission.split(":")
    pattern_parts = pattern.split(":")

    if len(pattern_parts) > len(perm_parts):
        return False

    for perm_part, pattern_part in zip(perm_parts, pattern_parts, strict=False):
        if pattern_part == "*":
            return True
        if perm_part != pattern_part:
            return False

    return len(pattern_parts) == len(perm_parts)


def serialize_user_context(user: UserContext) -> str:
    """Serialize UserContext to base64-encoded JSON for NATS headers.

    Args:
        user: UserContext to serialize

    Returns:
        Base64-encoded JSON string
    """
    json_str = user.model_dump_json()
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
    return encoded


def deserialize_user_context(encoded: str) -> UserContext:
    """Deserialize UserContext from base64-encoded JSON.

    Args:
        encoded: Base64-encoded JSON string

    Returns:
        UserContext instance

    Raises:
        ValueError: If deserialization fails
    """
    try:
        json_str = base64.b64decode(encoded.encode("ascii")).decode("utf-8")
        data = json.loads(json_str)
        return UserContext.model_validate(data)
    except Exception as e:
        raise ValueError(f"Failed to deserialize user context: {e}") from e


def set_user_context(user: UserContext | None) -> None:
    """Set user context for current async task.

    Args:
        user: UserContext to set, or None to clear
    """
    _user_context_var.set(user)


def get_user_context() -> UserContext | None:
    """Get user context for current async task.

    Can be used directly or as a fast_depends dependency:

    ```python
    from amirpc.context import CurrentUser

    # Using CurrentUser type alias (recommended)
    async def my_handler(payload: MyPayload, user: CurrentUser):
        if user:
            logger.info(f"Request from {user.email}")

    # Direct usage
    async def my_handler(payload: MyPayload):
        user = get_user_context()
        if user:
            logger.info(f"Request from {user.email}")
    ```

    Returns:
        UserContext if available, None otherwise
    """
    return _user_context_var.get()


# Type alias for dependency injection in handlers
CurrentUser = Annotated[UserContext | None, Depends(get_user_context)]


__all__ = [
    "USER_CONTEXT_HEADER",
    "CurrentUser",
    "UserContext",
    "deserialize_user_context",
    "get_user_context",
    "serialize_user_context",
    "set_user_context",
]

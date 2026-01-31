"""Runtime for dynamically creating FastAPI routes from gateway metadata."""

from __future__ import annotations

import importlib
import inspect
import json
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi import Path as PathParam

from amirpc.context import UserContext, set_user_context
from amirpc.types import AmiErrorEnvelope

if TYPE_CHECKING:
    from collections.abc import Callable

    from amirpc import Runtime

logger = getLogger(__name__)


class AutoGateway:
    """Auto-generates FastAPI routes from gateway_routes.json metadata.

    This runtime approach solves dependency issues by accepting gateway-specific
    dependencies (runtime, require_permission) as constructor parameters,
    avoiding the need to import them in generated code.

    Example:
        >>> from contextlib import asynccontextmanager
        >>> from fastapi import FastAPI
        >>> from amirpc import Runtime
        >>> from amirpc.gateway import AutoGateway
        >>> from my_gateway.auth import require_permission
        >>>
        >>> runtime = Runtime.from_env()
        >>>
        >>> @asynccontextmanager
        >>> async def lifespan(app: FastAPI):
        ...     await runtime.start()
        ...     yield
        ...     await runtime.stop()
        >>>
        >>> app = FastAPI(lifespan=lifespan)
        >>>
        >>> gateway = AutoGateway(
        ...     metadata_path="gateway_routes.json",
        ...     runtime=runtime,
        ...     require_permission=require_permission,
        ... )
        >>> app.include_router(gateway.router, prefix="/api/v1")
    """

    def __init__(
        self,
        metadata_path: str | Path,
        runtime: Runtime,
        require_permission: Callable[[str], Any],
        *,
        rpc_timeout: float = 5.0,
    ):
        """Initialize AutoGateway with metadata and dependencies.

        Args:
            metadata_path: Path to gateway_routes.json file
            runtime: Runtime instance (must be started before handling requests)
            require_permission: Function that creates permission dependency
            rpc_timeout: Timeout for RPC requests in seconds (default: 5.0)
        """
        self.metadata_path = Path(metadata_path)
        self.runtime = runtime
        self.require_permission = require_permission
        self.rpc_timeout = rpc_timeout
        self.router = APIRouter()
        self._openapi_tags: list[dict[str, Any]] = []

        # Load metadata and create routes
        self._load_and_create_routes()

    def get_openapi_tags(self) -> list[dict[str, Any]]:
        """Get OpenAPI tags metadata with descriptions.

        Returns:
            List of tag dictionaries for OpenAPI spec customization
        """
        return self._openapi_tags

    def _load_metadata(self) -> dict[str, Any]:
        """Load gateway metadata from JSON file."""
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Gateway metadata not found: {self.metadata_path}")

        with open(self.metadata_path, encoding="utf-8") as f:
            return json.load(f)

    def _load_and_create_routes(self) -> None:
        """Load metadata and create all FastAPI routes."""
        metadata = self._load_metadata()
        services = metadata.get("services", {})

        logger.info(
            f"AutoGateway: Loaded metadata for {len(services)} services: {', '.join(services.keys())}"
        )

        for service_name, service_meta in services.items():
            self._create_service_routes(service_name, service_meta)

    def _create_service_routes(
        self, service_name: str, service_meta: dict[str, Any]
    ) -> None:
        """Create routes for a single service."""
        client_module_name = service_meta["client_module"]
        client_class_name = service_meta["client_class"]

        # Dynamically import client class
        client_module = importlib.import_module(client_module_name)
        client_class = getattr(client_module, client_class_name)

        namespaces = service_meta.get("namespaces", {})
        for namespace_name, namespace_meta in namespaces.items():
            self._create_namespace_routes(
                service_name,
                namespace_name,
                namespace_meta,
                client_class,
            )

    def _create_namespace_routes(
        self,
        service_name: str,
        namespace_name: str,
        namespace_meta: dict[str, Any],
        client_class: type,
    ) -> None:
        """Create routes for a namespace."""
        prefix = namespace_meta["prefix"]

        # Use human-readable tag name instead of technical ID
        tag_name = namespace_meta.get(
            "tag_name", namespace_meta.get("tag", namespace_name)
        )
        tag_description = namespace_meta.get("tag_description")

        # Add tag to OpenAPI tags metadata
        tag_info: dict[str, Any] = {"name": tag_name}
        if tag_description:
            tag_info["description"] = tag_description
        self._openapi_tags.append(tag_info)

        # Create sub-router for this namespace with human-readable tag
        ns_router = APIRouter(prefix=prefix, tags=[tag_name])

        endpoints = namespace_meta.get("endpoints", [])
        logger.info(
            f"AutoGateway: Creating {len(endpoints)} endpoints for {service_name}.{namespace_name} (prefix={prefix})"
        )

        for endpoint_meta in endpoints:
            self._create_endpoint(ns_router, endpoint_meta, client_class)

        # Include namespace router in main router
        self.router.include_router(ns_router)

    def _resolve_type(
        self, type_str: str, module_name: str | None = None
    ) -> type | Any:
        """Resolve type string to actual Python type.

        Args:
            type_str: Type as string (e.g., "str", "UUID", "list[Worker]")
            module_name: Module to import type from (if needed)

        Returns:
            Actual Python type
        """
        from uuid import UUID

        # Handle built-in types
        type_map = {
            "str": str,
            "int": int,
            "bool": bool,
            "float": float,
            "UUID": UUID,
        }

        if type_str in type_map:
            return type_map[type_str]

        # Handle Optional types - extract inner type and pass module through
        if type_str.startswith("Optional["):
            inner_type_str = type_str[9:-1]
            inner_type = self._resolve_type(inner_type_str, module_name)
            return Optional[inner_type]  # noqa: UP045 - runtime type construction

        # Handle list types - extract inner type and pass module through
        if type_str.startswith("list["):
            inner_type_str = type_str[5:-1]
            inner_type = self._resolve_type(inner_type_str, module_name)
            return list[inner_type]  # ty: ignore[invalid-type-form]

        # Import from module if specified
        if module_name:
            try:
                mod = importlib.import_module(module_name)
                resolved = getattr(mod, type_str)
                logger.debug(
                    f"AutoGateway: Resolved type {type_str} from {module_name}"
                )
                return resolved
            except (ImportError, AttributeError) as e:
                logger.warning(
                    f"AutoGateway: Failed to import {type_str} from {module_name}: {e}"
                )

        # Fallback: return Any
        return Any

    def _create_endpoint(
        self,
        router: APIRouter,
        endpoint_meta: dict[str, Any],
        client_class: type,
    ) -> None:
        """Create a single FastAPI endpoint from metadata with proper type annotations."""
        http_method = endpoint_meta["http_method"].lower()
        http_path = endpoint_meta["http_path"]
        rpc_namespace = endpoint_meta["rpc_namespace"]
        rpc_method = endpoint_meta["rpc_method"]
        permission = endpoint_meta.get("permission")
        summary = endpoint_meta.get("summary", "")
        status_code = endpoint_meta.get("status_code", 200)
        params_meta = endpoint_meta.get("params", [])
        returns_meta = endpoint_meta.get("returns")

        # Capture rpc_timeout from self for closure
        rpc_timeout = self.rpc_timeout

        # Log endpoint creation with parameter details
        param_types = ", ".join([f"{p['name']}: {p['type']}" for p in params_meta])
        logger.debug(
            f"AutoGateway: Creating endpoint {http_method.upper()} {http_path} -> "
            f"{rpc_namespace}.{rpc_method}({param_types})"
        )

        # Build parameter signature
        param_annotations: dict[str, type] = {}
        param_defaults: dict[str, Any] = {}

        # Process each parameter
        for param in params_meta:
            param_name = param["name"]
            param_type = self._resolve_type(param["type"], param.get("module"))
            param_in = param["in"]
            param_required = param.get("required", True)

            # Create FastAPI parameter with proper annotation
            if param_in == "path":
                param_defaults[param_name] = PathParam(...)
            elif param_in == "query":
                param_defaults[param_name] = (
                    Query(...) if param_required else Query(None)
                )
            elif param_in == "body":
                # embed=True wraps body in {"param_name": value} structure
                param_defaults[param_name] = (
                    Body(..., embed=True) if param_required else Body(None, embed=True)
                )
            else:
                param_defaults[param_name] = ...

            param_annotations[param_name] = param_type

        # Add user parameter if permission is required (injected via require_permission)
        # The user will be available as KeycloakUser from gateway auth
        if permission:
            # We use Any here because we can't import KeycloakUser from gateway
            # The actual type will be KeycloakUser from require_permission dependency
            param_annotations["user"] = Any
            param_defaults["user"] = Depends(self.require_permission(permission))

        # Capture runtime reference for closure
        runtime = self.runtime

        # Build endpoint function with proper signature
        async def endpoint_handler(**kwargs: Any) -> Any:
            """Dynamically created endpoint handler."""
            # Extract and convert user context if present
            user = kwargs.pop("user", None)
            if user is not None:
                # Convert KeycloakUser to UserContext
                # KeycloakUser has: id, email, username, roles, permissions, organization
                # Organization structure from Keycloak: {"OrgName": {"id": "uuid"}}
                org_name = None
                org_id = None
                if isinstance(user.organization, dict) and user.organization:
                    # Get first organization (users typically have one)
                    org_name = next(iter(user.organization.keys()))
                    org_data = user.organization[org_name]
                    if isinstance(org_data, dict):
                        org_id = org_data.get("id")

                user_context = UserContext(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    roles=user.roles,
                    permissions=user.permissions,
                    organization_name=org_name,
                    organization_id=org_id,
                )
                # Set in context variable for propagation to services
                set_user_context(user_context)
            else:
                # Clear user context if no user
                set_user_context(None)

            # Create client instance via runtime
            client = runtime.client(client_class)  # ty: ignore[invalid-argument-type]

            # Get namespace and method
            ns = getattr(client, rpc_namespace)
            method = getattr(ns, rpc_method)

            # Call RPC method with parameters (user already popped)
            # Pass rpc_timeout if method accepts it
            sig = inspect.signature(method)
            if "rpc_timeout" in sig.parameters:
                result = await method(**kwargs, rpc_timeout=rpc_timeout)
            else:
                result = await method(**kwargs)

            # For 204 No Content, don't return anything
            if status_code == 204:
                return None

            return result

        # Build function signature with proper parameter types
        parameters = []
        for param_name in param_annotations:
            param_type = param_annotations[param_name]
            param_default = param_defaults[param_name]

            parameters.append(
                inspect.Parameter(
                    name=param_name,
                    kind=inspect.Parameter.KEYWORD_ONLY,
                    annotation=param_type,
                    default=param_default,
                )
            )

        # Set proper signature
        endpoint_handler.__signature__ = inspect.Signature(parameters)  # type: ignore
        endpoint_handler.__annotations__ = param_annotations

        # Set function metadata
        endpoint_handler.__name__ = endpoint_meta["name"]

        # Build description with permission info
        description_parts = []
        if endpoint_meta.get("doc"):
            description_parts.append(endpoint_meta["doc"])

        if permission:
            description_parts.append(f"\n**Required Permission:** `{permission}`")

        endpoint_handler.__doc__ = (
            "\n".join(description_parts) if description_parts else None
        )

        # Build route kwargs
        route_kwargs: dict[str, Any] = {
            "summary": summary,
            "status_code": status_code,
        }

        # Set response_model
        if status_code == 204:
            route_kwargs["response_model"] = None
        elif returns_meta and returns_meta.get("type"):
            return_type = self._resolve_type(
                returns_meta["type"], returns_meta.get("module")
            )
            route_kwargs["response_model"] = return_type

        # Add error responses to OpenAPI schema with AmiErrorEnvelope model
        # This generates proper OpenAPI schemas for all error responses
        error_responses_meta = endpoint_meta.get("error_responses", {})
        if error_responses_meta:
            responses = {}
            for status, error_info in error_responses_meta.items():
                responses[int(status)] = {
                    "description": error_info.get("description", "Error"),
                    "model": AmiErrorEnvelope,  # All errors use standard envelope format
                }
            route_kwargs["responses"] = responses

        # Permission dependency is now handled via user parameter injection above
        # (see param_defaults["user"] = Depends(self.require_permission(permission)))

        # Register route with FastAPI router
        route_method = getattr(router, http_method)
        route_method(http_path, **route_kwargs)(endpoint_handler)


__all__ = ["AutoGateway"]

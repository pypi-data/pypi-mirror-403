"""FastAPI gateway metadata generation from ASL specifications."""

import json
from pathlib import Path
from typing import Any

from amic.ast.model import ErrorDecl, InlineStruct, Namespace, Rpc, Service, TypeRef
from amic.codegen.http_mapping import (
    HttpMetadata,
    extract_http_metadata,
    extract_path_parameters,
    has_http_endpoints,
    normalize_router_prefix,
)
from amic.codegen.utils import py_type, response_result_name, snake
from amic.compilation.compiled import CompiledProject

# Well-known errors with standard HTTP status codes
WELL_KNOWN_ERROR_STATUS = {
    # 4xx Client Errors
    "BadRequest": 400,
    "InvalidArgument": 400,
    "Unauthorized": 401,
    "Forbidden": 403,
    "NotFound": 404,
    "Conflict": 409,
    "ValidationError": 422,
    "RateLimited": 429,
    # 5xx Server Errors
    "InternalError": 500,
    "ServiceUnavailable": 503,
}

# Well-known error descriptions
WELL_KNOWN_ERROR_DESCRIPTIONS = {
    "BadRequest": "Bad Request - The request is malformed or invalid",
    "InvalidArgument": "Bad Request - Invalid request parameters",
    "Unauthorized": "Unauthorized - Missing or invalid authentication token",
    "Forbidden": "Forbidden - Insufficient permissions",
    "NotFound": "Not Found - The requested resource does not exist",
    "Conflict": "Conflict - Resource conflict",
    "ValidationError": "Unprocessable Entity - Validation failed",
    "RateLimited": "Too Many Requests - Rate limit exceeded",
    "InternalError": "Internal Server Error - An unexpected error occurred",
    "ServiceUnavailable": "Service Unavailable - Service is temporarily unavailable",
}


def get_error_http_status(error_name: str, error_decls: dict[str, ErrorDecl]) -> int:
    """Get HTTP status code for an error.

    Args:
        error_name: Name of the error
        error_decls: Map of error name to ErrorDecl

    Returns:
        HTTP status code (default 400 if not specified)
    """
    # Check well-known errors first
    if error_name in WELL_KNOWN_ERROR_STATUS:
        return WELL_KNOWN_ERROR_STATUS[error_name]

    # Check custom error declarations
    if error_name in error_decls:
        error_decl = error_decls[error_name]
        # Look for http_status attribute
        for attr in error_decl.attrs:
            if attr.name == "http_status" and attr.args:
                return int(attr.args[0])

    # Default to 400 Bad Request
    return 400


def get_error_description(
    error_name: str, http_status: int, permission: str | None = None
) -> str:
    """Get human-readable description for an error.

    Args:
        error_name: Name of the error
        http_status: HTTP status code
        permission: Permission requirement (for Forbidden errors)

    Returns:
        Error description
    """
    # Special case for Forbidden with permission
    if error_name == "Forbidden" and permission:
        return f"Forbidden - Missing required permission: `{permission}`"

    # Check well-known errors
    if error_name in WELL_KNOWN_ERROR_DESCRIPTIONS:
        return WELL_KNOWN_ERROR_DESCRIPTIONS[error_name]

    # Generate description from error name and status
    status_text = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }.get(http_status, f"HTTP {http_status}")

    # Convert CamelCase to readable text
    import re

    readable_name = re.sub(r"([A-Z])", r" \1", error_name).strip()

    return f"{status_text} - {readable_name}"


def build_error_responses_metadata(
    permission: str | None, throws: list[str], error_decls: dict[str, ErrorDecl]
) -> dict[int, dict[str, Any]]:
    """Build metadata for HTTP error responses.

    Args:
        permission: Permission required for the endpoint (if any)
        throws: List of error types that can be thrown
        error_decls: Map of error name to ErrorDecl

    Returns:
        Dictionary mapping HTTP status codes to error metadata
    """
    error_responses = {}

    # Add 401 Unauthorized if permission is required
    if permission:
        error_responses[401] = {
            "description": WELL_KNOWN_ERROR_DESCRIPTIONS["Unauthorized"],
            "error_type": "Unauthorized",
        }
        error_responses[403] = {
            "description": f"Forbidden - Missing required permission: `{permission}`",
            "error_type": "Forbidden",
        }

    # Add error responses based on throws
    for error_name in throws:
        if error_name == "Unauthorized":
            # Already added above with permission
            continue

        # Get HTTP status from error declaration or well-known mapping
        http_status = get_error_http_status(error_name, error_decls)

        # Get description
        description = get_error_description(
            error_name, http_status, permission if error_name == "Forbidden" else None
        )

        # Add to responses (later errors with same status code override earlier ones)
        error_responses[http_status] = {
            "description": description,
            "error_type": error_name,
        }

    # Always add 500 Internal Server Error
    if 500 not in error_responses:
        error_responses[500] = {
            "description": WELL_KNOWN_ERROR_DESCRIPTIONS["InternalError"],
            "error_type": "InternalError",
        }

    return error_responses


def get_type_module(typ: TypeRef, service: Service) -> str | None:
    """Extract module path for a TypeRef, handling Optional and list wrappers.

    Args:
        typ: TypeRef to analyze
        service: Service containing the type

    Returns:
        Module path (e.g., "amirpc_specs.indexer.models") or None for builtins
    """
    # Handle container types (list[T]) - recursively get module from inner type
    if typ.kind == "container" and typ.name == "list" and typ.args:
        return get_type_module(typ.args[0], service)

    # Builtin and well-known types don't need module
    if typ.kind in {"builtin", "well_known"}:
        return None

    # Model, error, enum types need module
    if typ.kind in {"model", "error", "enum"}:
        return f"amirpc_specs.{snake(service.name)}.models"

    return None


def build_endpoint_metadata(
    service: Service,
    namespace: Namespace,
    rpc: Rpc,
    http_meta: HttpMetadata,
    error_decls: dict[str, ErrorDecl],
) -> dict[str, Any]:
    """Build metadata dictionary for a single HTTP endpoint.

    Returns:
        Dictionary containing endpoint configuration for runtime loading.
    """
    path_params = extract_path_parameters(http_meta.path)

    # Compute relative path for FastAPI route
    router_prefix = normalize_router_prefix(service.name, namespace.name)
    if http_meta.path.startswith(router_prefix):
        relative_path = http_meta.path[len(router_prefix) :]
    else:
        relative_path = http_meta.path

    if relative_path and not relative_path.startswith("/"):
        relative_path = "/" + relative_path
    elif not relative_path:
        relative_path = "/"

    # Build parameters metadata
    params_metadata = []
    for param in rpc.params:
        param_module = (
            get_type_module(param.type, service)
            if isinstance(param.type, TypeRef)
            else None
        )

        param_meta = {
            "name": param.name,
            "type": py_type(param.type),
            "in": "path"
            if param.name in path_params
            else ("query" if http_meta.method in {"GET", "DELETE", "HEAD"} else "body"),
            "required": not (isinstance(param.type, TypeRef) and param.type.optional),
            "doc": getattr(param, "doc", None),
            "module": param_module,
        }
        params_metadata.append(param_meta)

    # Build return type metadata
    if isinstance(rpc.returns, InlineStruct):
        # Check if empty inline struct (void response)
        if not rpc.returns.fields:
            return_type = None
            return_module = None
        else:
            ns_path = [snake(namespace.name)]
            return_type = response_result_name(service, rpc, ns_path)
            return_module = f"amirpc_specs.{snake(service.name)}.{'.'.join(ns_path)}"
    elif isinstance(rpc.returns, TypeRef):
        return_type = py_type(rpc.returns) if rpc.returns.name != "None" else None
        # Determine module for non-builtin types
        if (
            rpc.returns.kind not in {"builtin", "well_known"}
            and rpc.returns.name != "None"
        ):
            return_module = f"amirpc_specs.{snake(service.name)}.models"
        else:
            return_module = None
    else:
        return_type = None
        return_module = None

    # Extract throws list
    throws = []
    for attr in rpc.attrs:
        if attr.name == "throws":
            throws.extend([str(x) for x in attr.args])

    # Build summary
    summary = (
        getattr(rpc, "doc", "").strip().splitlines()[0]
        if getattr(rpc, "doc", None)
        else rpc.name
    )

    # Determine status code
    if not return_type:
        # No return type - use 204 No Content
        status_code = 204
    else:
        # Has return type - use 200 OK
        status_code = 200

    # Build error responses metadata
    error_responses = build_error_responses_metadata(
        http_meta.permission, throws, error_decls
    )

    return {
        "name": snake(rpc.name),
        "rpc_namespace": snake(namespace.name),
        "rpc_method": snake(rpc.name),
        "http_method": http_meta.method,
        "http_path": relative_path,
        "permission": http_meta.permission,
        "params": params_metadata,
        "returns": {
            "type": return_type,
            "module": return_module,
        }
        if return_type
        else None,
        "summary": summary,
        "doc": getattr(rpc, "doc", None),
        "throws": throws,
        "status_code": status_code,
        "error_responses": error_responses,
    }


def build_namespace_metadata(
    service: Service,
    namespace: Namespace,
    error_decls: dict[str, ErrorDecl],
) -> dict[str, Any] | None:
    """Build metadata dictionary for a namespace.

    Returns None if namespace has no HTTP endpoints.
    """
    if not has_http_endpoints(namespace):
        return None

    endpoints = []
    for item in namespace.items:
        if isinstance(item, Rpc):
            http_meta = extract_http_metadata(item)
            if http_meta:
                endpoint_meta = build_endpoint_metadata(
                    service, namespace, item, http_meta, error_decls
                )
                endpoints.append(endpoint_meta)

    if not endpoints:
        return None

    router_prefix = normalize_router_prefix(service.name, namespace.name)

    # Generate human-readable tag name
    tag_name = f"{service.name} - {namespace.name}"

    # Generate tag description from namespace or service docstring
    tag_description = None
    if namespace.doc:
        tag_description = namespace.doc.strip()
    elif service.doc:
        # Fallback to service description
        tag_description = service.doc.strip()

    # Keep technical tag ID for backwards compatibility (used in permission checks)
    tag_id = f"{snake(service.name)}:{snake(namespace.name)}"

    return {
        "prefix": router_prefix,
        "tag_id": tag_id,  # Technical ID (orchestrator:workers)
        "tag_name": tag_name,  # Human-readable name (Orchestrator - Workers)
        "tag_description": tag_description,  # Description from docstrings
        "endpoints": endpoints,
    }


def build_service_metadata(
    service: Service, error_decls: dict[str, ErrorDecl]
) -> dict[str, Any] | None:
    """Build metadata dictionary for a service.

    Returns None if service has no HTTP endpoints.
    """
    namespaces_meta = {}

    for ns in getattr(service, "namespaces", []) or []:
        ns_meta = build_namespace_metadata(service, ns, error_decls)
        if ns_meta:
            namespaces_meta[ns.name] = ns_meta

    if not namespaces_meta:
        return None

    service_snake = snake(service.name)

    # Extract service description from docstring
    service_description = service.doc.strip() if service.doc else None

    return {
        "name": service.name,
        "description": service_description,
        "client_module": f"amirpc_specs.{service_snake}",
        "client_class": f"{service.name}Client",
        "namespaces": namespaces_meta,
    }


def generate_gateway_metadata(
    project: CompiledProject, specs_out_dir: Path
) -> Path | None:
    """Generate gateway_routes.json metadata file for runtime loading.

    Generates a JSON file containing all HTTP endpoint metadata that the
    AutoGateway runtime will use to dynamically create FastAPI routes.

    Returns:
        Path to generated gateway_routes.json or None if no HTTP endpoints found.
    """
    # Build error declarations registry (name -> ErrorDecl)
    error_decls: dict[str, ErrorDecl] = {}

    # Add domain errors
    for error in project.domain_errors:
        error_decls[error.name] = error

    # Add local errors from each service
    for svc in project.services:
        for error in svc.local_errors:
            error_decls[error.name] = error

    services_metadata = {}

    # Build metadata for each service
    for svc in project.services:
        service_meta = build_service_metadata(svc.service, error_decls)
        if service_meta:
            services_metadata[svc.service.name] = service_meta

    if not services_metadata:
        return None

    # Create metadata structure
    metadata = {
        "version": "1.0",
        "generated_by": "amic",
        "services": services_metadata,
    }

    # Write to JSON file
    output_path = specs_out_dir / "gateway_routes.json"
    output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return output_path


__all__ = [
    "build_endpoint_metadata",
    "build_namespace_metadata",
    "build_service_metadata",
    "generate_gateway_metadata",
]

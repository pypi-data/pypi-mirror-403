"""HTTP mapping utilities for gateway code generation."""

from dataclasses import dataclass

from amic.ast.model import Namespace, Rpc


@dataclass
class HttpMetadata:
    """HTTP metadata extracted from RPC declaration."""

    method: str  # GET, POST, PATCH, DELETE, etc.
    path: str  # /posts, /posts/{id}, etc.
    permission: str | None = None  # blog:posts:create


def extract_http_metadata(rpc: Rpc) -> HttpMetadata | None:
    """Extract HTTP metadata from RPC attributes.

    Returns None if RPC doesn't have @http decorator.
    """
    http_attr = None
    permission_attr = None

    for attr in rpc.attrs:
        if attr.name == "http":
            http_attr = attr
        elif attr.name == "permission":
            permission_attr = attr

    if http_attr is None:
        # No @http decorator - this RPC is not exposed via HTTP
        return None

    # Extract method and path from @http
    method = http_attr.kwargs.get("method", "POST")
    path = http_attr.kwargs.get("path", "")

    # Extract permission if present
    permission = None
    if permission_attr and permission_attr.args:
        permission = str(permission_attr.args[0])

    return HttpMetadata(
        method=str(method).upper(),
        path=str(path),
        permission=permission,
    )


def has_http_endpoints(namespace: Namespace) -> bool:
    """Check if namespace has any RPC methods with @http decorator."""
    for item in namespace.items:
        if isinstance(item, Rpc):
            if extract_http_metadata(item) is not None:
                return True
    return False


def extract_path_parameters(path: str) -> list[str]:
    """Extract path parameter names from URL path.

    Example: "/posts/{post_id}/comments/{comment_id}" -> ["post_id", "comment_id"]
    """
    import re

    pattern = r"\{([^}]+)\}"
    return re.findall(pattern, path)


def normalize_router_prefix(service_name: str, namespace_name: str) -> str:
    """Generate router prefix from service and namespace names.

    Example: ("Blog", "Posts") -> "/blog/posts"
    """
    from amic.codegen.utils import snake

    service_slug = snake(service_name)
    namespace_slug = snake(namespace_name)

    return f"/{service_slug}/{namespace_slug}"


__all__ = [
    "HttpMetadata",
    "extract_http_metadata",
    "extract_path_parameters",
    "has_http_endpoints",
    "normalize_router_prefix",
]

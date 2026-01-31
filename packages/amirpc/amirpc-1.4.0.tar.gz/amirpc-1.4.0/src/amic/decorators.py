# Temporary facade until full move of decorators to top-level (see REFACTORPLAN step 6)
from collections.abc import Callable
from pathlib import Path

from amic.ast.model import (
    Attribute,
    Decorator,
    ErrorDecl,
    Event,
    Infrastructure,
    InfrastructureFile,
    InlineStruct,
    Model,
    ModelField,
    ModuleFile,
    Namespace,
    Param,
    ReturnField,
    Rpc,
    Service,
)
from amic.errors import AmiToolCompileError as AmiCompileError
from amic.locate import find_line as locate_find_line
from amic.locate import locate_header_line


def _ensure_attrs_list(node: object) -> list[Attribute]:
    if isinstance(node, Infrastructure):
        if node.attrs is None:
            node.attrs = []
        return node.attrs
    return node.attrs


def _dec_throws(node: object, dec: Decorator) -> None:
    if not isinstance(node, Rpc):
        raise AmiCompileError(
            "@throws is only allowed on RPC declarations", stage="decorate"
        )
    _ensure_attrs_list(node).append(
        Attribute(
            name="throws", args=list(dec.args), kwargs=dict(dec.kwargs), inline=False
        )
    )


def _dec_subject(node: object, dec: Decorator) -> None:
    if not isinstance(node, Infrastructure):
        raise AmiCompileError(
            "@subject is only allowed on infrastructure", stage="decorate"
        )
    if not dec.args and "value" not in dec.kwargs:
        raise AmiCompileError("@subject requires a string argument", stage="decorate")
    val = str(dec.args[0]) if dec.args else str(dec.kwargs["value"])
    _ensure_attrs_list(node).append(
        Attribute(name="subject", args=[val], kwargs={}, inline=False)
    )


def _dec_pydantic(node: object, dec: Decorator) -> None:
    # Allowed on: model field, rpc/ev param, inline return field
    if not isinstance(node, (ModelField, Param, ReturnField)):
        raise AmiCompileError(
            "@pydantic is only allowed on fields/params", stage="decorate"
        )
    if dec.args:
        raise AmiCompileError(
            "@pydantic accepts only keyword arguments (default, default_factory)",
            stage="decorate",
        )
    allowed = {"default", "default_factory"}
    unknown = [k for k in dec.kwargs.keys() if k not in allowed]
    if unknown:
        raise AmiCompileError(
            f"@pydantic: unsupported keyword(s): {', '.join(unknown)}",
            stage="decorate",
        )
    attrs = _ensure_attrs_list(node)
    # Append so that these override earlier inline attrs (field_kwargs_from_attrs walks reversed)
    for key in ("default", "default_factory"):
        if key in dec.kwargs:
            val = dec.kwargs[key]
            attrs.append(Attribute(name=key, args=[val], kwargs={}, inline=False))


def _dec_http(node: object, dec: Decorator) -> None:
    """Handle @http decorator for RPC declarations.

    Example: @http(method: "POST", path: "/posts")
    """
    if not isinstance(node, Rpc):
        raise AmiCompileError(
            "@http is only allowed on RPC declarations", stage="decorate"
        )

    # Validate required arguments
    method = dec.kwargs.get("method")
    path = dec.kwargs.get("path")

    if not method:
        raise AmiCompileError(
            "@http requires 'method' keyword argument (e.g., method=\"POST\")",
            stage="decorate",
        )

    if path is None:
        raise AmiCompileError(
            '@http requires \'path\' keyword argument (e.g., path="/posts" or path="" for root)',
            stage="decorate",
        )

    # Validate HTTP method
    valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    method_upper = str(method).upper()
    if method_upper not in valid_methods:
        raise AmiCompileError(
            f"@http: invalid method '{method}'. Must be one of: {', '.join(valid_methods)}",
            stage="decorate",
        )

    # Store as attribute
    _ensure_attrs_list(node).append(
        Attribute(
            name="http",
            args=[],
            kwargs={"method": method_upper, "path": str(path)},
            inline=False,
        )
    )


def _dec_targeted(node: object, dec: Decorator) -> None:
    """Handle @targeted decorator for RPC declarations.

    Marks RPC as targeted to a specific service instance.
    Example: @targeted
    """
    if not isinstance(node, Rpc):
        raise AmiCompileError(
            "@targeted is only allowed on RPC declarations", stage="decorate"
        )

    if dec.args or dec.kwargs:
        raise AmiCompileError(
            "@targeted does not accept any arguments", stage="decorate"
        )

    _ensure_attrs_list(node).append(
        Attribute(name="targeted", args=[], kwargs={}, inline=False)
    )


def _dec_permission(node: object, dec: Decorator) -> None:
    """Handle @permission decorator for RPC declarations.

    Example: @permission("blog:posts:create")
    Automatically adds Unauthorized to @throws if not already present.
    """
    if not isinstance(node, Rpc):
        raise AmiCompileError(
            "@permission is only allowed on RPC declarations", stage="decorate"
        )

    # Get permission string from first argument or 'value' kwarg
    permission = None
    if dec.args:
        permission = str(dec.args[0])
    elif "value" in dec.kwargs:
        permission = str(dec.kwargs["value"])
    else:
        raise AmiCompileError(
            '@permission requires a permission string (e.g., @permission("blog:posts:create"))',
            stage="decorate",
        )

    attrs = _ensure_attrs_list(node)

    # Store permission as attribute
    attrs.append(
        Attribute(name="permission", args=[permission], kwargs={}, inline=False)
    )

    # Automatically add Unauthorized to @throws if not already present
    # Find existing @throws attribute
    throws_attr = None
    for attr in attrs:
        if attr.name == "throws":
            throws_attr = attr
            break

    if throws_attr is None:
        # No @throws yet, create one with Unauthorized
        attrs.append(
            Attribute(name="throws", args=["Unauthorized"], kwargs={}, inline=False)
        )
    else:
        # Check if Unauthorized already in throws
        if "Unauthorized" not in throws_attr.args:
            # Add Unauthorized to existing throws
            throws_attr.args.append("Unauthorized")


DECORATOR_REGISTRY: dict[str, Callable[[object, Decorator], None]] = {
    "throws": _dec_throws,
    "subject": _dec_subject,
    "pydantic": _dec_pydantic,
    "http": _dec_http,
    "permission": _dec_permission,
    "targeted": _dec_targeted,
}


def _node_kind(obj: object) -> str:
    if isinstance(obj, Model):
        return "Model"
    if isinstance(obj, ModelField):
        return "Field"
    if isinstance(obj, Service):
        return "Service"
    if isinstance(obj, Rpc):
        return "Rpc"
    if isinstance(obj, Event):
        return "Event"
    if isinstance(obj, Param):
        return "Param"
    if isinstance(obj, ReturnField):
        return "ReturnField"
    if isinstance(obj, ErrorDecl):
        return "ErrorDecl"
    if isinstance(obj, Infrastructure):
        return "Infrastructure"
    if isinstance(obj, Namespace):
        return "Namespace"
    return type(obj).__name__


def apply_decorators_on_node(node: object, file: Path) -> None:
    decs = getattr(node, "decorators", None)
    if not decs:
        return
    kind = _node_kind(node)
    for dec in decs:
        handler = DECORATOR_REGISTRY.get(dec.name)
        if handler is None:
            line_hint: int | None = locate_find_line(file, f"@{dec.name}")
            raise AmiCompileError(
                f"Unknown decorator @{dec.name} on {kind}",
                file=file,
                line=line_hint,
                stage="decorate",
            )
        try:
            handler(node, dec)
        except AmiCompileError as ex:
            header_line = locate_header_line(file, node)
            dec_line = locate_find_line(file, f"@{dec.name}") or header_line
            raise AmiCompileError(
                ex.message,
                file=file,
                line=dec_line,
                column=None,
                stage="decorate",
                hint=getattr(ex, "hint", None)
                or f"While applying @{dec.name} on {kind}",
                notes=getattr(ex, "notes", None),
                cause=ex,
            )
    try:
        node.decorators = None
    except Exception:
        pass


def _apply_decorators_to_node(obj: object, *, file: Path) -> None:
    if isinstance(obj, Model):
        apply_decorators_on_node(obj, file)
        for f in obj.fields:
            apply_decorators_on_node(f, file)
    elif isinstance(obj, Rpc):
        apply_decorators_on_node(obj, file)
        for p in obj.params:
            apply_decorators_on_node(p, file)
        if isinstance(obj.returns, InlineStruct):
            for rf in obj.returns.fields:
                apply_decorators_on_node(rf, file)
    elif isinstance(obj, Service):
        apply_decorators_on_node(obj, file)
        for r in obj.rpcs:
            apply_decorators_on_node(r, file)
            for p in r.params:
                apply_decorators_on_node(p, file)
            if isinstance(r.returns, InlineStruct):
                for rf in r.returns.fields:
                    apply_decorators_on_node(rf, file)
        for ev in getattr(obj, "emits", []) or []:
            apply_decorators_on_node(ev, file)
            for p in ev.params:
                apply_decorators_on_node(p, file)
        for ev in getattr(obj, "listens", []) or []:
            apply_decorators_on_node(ev, file)
            for p in ev.params:
                apply_decorators_on_node(p, file)
        for ns in getattr(obj, "namespaces", []) or []:
            _apply_decorators_to_node(ns, file=file)
    elif isinstance(obj, Event):
        apply_decorators_on_node(obj, file)
        for p in obj.params:
            apply_decorators_on_node(p, file)
    elif isinstance(obj, Namespace):
        apply_decorators_on_node(obj, file)
        for it in getattr(obj, "items", []) or []:
            _apply_decorators_to_node(it, file=file)
    elif isinstance(obj, ErrorDecl):
        apply_decorators_on_node(obj, file)
        for p in obj.params:
            apply_decorators_on_node(p, file)
    elif isinstance(obj, Infrastructure):
        apply_decorators_on_node(obj, file)


def apply_decorators_parsed(
    ast: InfrastructureFile | Infrastructure | ModuleFile, *, file: Path
) -> None:
    if isinstance(ast, InfrastructureFile):
        if ast.infrastructure:
            _apply_decorators_to_node(ast.infrastructure, file=file)
        for d in ast.decls:
            _apply_decorators_to_node(d, file=file)
    elif isinstance(ast, Infrastructure):
        _apply_decorators_to_node(ast, file=file)
    elif isinstance(ast, ModuleFile):
        for d in ast.decls:
            _apply_decorators_to_node(d, file=file)


__all__ = [
    "DECORATOR_REGISTRY",
    "apply_decorators_parsed",
]

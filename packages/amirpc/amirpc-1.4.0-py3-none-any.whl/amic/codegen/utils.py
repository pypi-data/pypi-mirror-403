"""Shared codegen utilities: naming, typing and imports helpers."""

import ast
from collections.abc import Iterable

from amic.ast.model import (
    Attribute,
    Event,
    InlineStruct,
    Namespace,
    Rpc,
    Service,
    TypeRef,
)
from amic.codegen.wellknown import get_import_info, get_python_type
from amic.compilation.compiled import WELL_KNOWN_TYPES


def snake(name: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and (not name[i - 1].isupper()):
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def ns_prefix_pascal(ns_path: list[str] | tuple[str, ...] | None) -> str:
    if not ns_path:
        return ""
    return "".join(seg.capitalize() for seg in "_".join(ns_path).split("_"))


def ns_prefix_snake(ns_path: list[str] | tuple[str, ...] | None) -> str:
    if not ns_path:
        return ""
    return "_".join(ns_path)


_BUILTIN_TYPE_MAP: dict[str, str] = {
    "int": "int",
    "string": "str",
    "bool": "bool",
    "float": "float",
}


def py_type(typ: TypeRef) -> str:
    if typ.kind == "builtin":
        base = _BUILTIN_TYPE_MAP[typ.name]
        return f"Optional[{base}]" if getattr(typ, "optional", False) else base
    if typ.kind == "well_known":
        base = get_python_type(typ.name)
        return f"Optional[{base}]" if getattr(typ, "optional", False) else base
    # no extra normalization for model names; resolver must set kind='well_known'
    if typ.kind == "container" and typ.name == "list":
        inner = typ.args[0] if typ.args else TypeRef(name="Any", kind="unresolved")
        base = f"list[{py_type(inner)}]"
        return f"Optional[{base}]" if getattr(typ, "optional", False) else base
    if typ.kind in {"model", "error", "enum"}:
        base = typ.name
        return f"Optional[{base}]" if getattr(typ, "optional", False) else base
    base = typ.name
    return f"Optional[{base}]" if getattr(typ, "optional", False) else base


def is_builtin_or_well_known(typ: TypeRef) -> bool:
    # list[...] з примітивом або well-known усередині — також скаляроподібний для генерації
    if typ.kind in {"builtin", "well_known"}:
        return True
    if typ.kind == "container" and typ.name == "list" and typ.args:
        return is_builtin_or_well_known(typ.args[0])
    return False


def type_expr(typ: TypeRef) -> ast.expr:
    """Build a Python AST expression for a given TypeRef.

    Supports containers like list[T], mapping builtins and well-known types.
    """

    def _wrap_optional(node: ast.expr) -> ast.expr:
        return (
            ast.Subscript(value=ast.Name(id="Optional"), slice=node, ctx=ast.Load())
            if getattr(typ, "optional", False)
            else node
        )

    if typ.kind == "builtin":
        return _wrap_optional(ast.Name(id=_BUILTIN_TYPE_MAP[typ.name]))
    if typ.kind == "well_known":
        # Normalize well-known names to their Python types (e.g., Datetime -> datetime)
        return _wrap_optional(ast.Name(id=get_python_type(typ.name)))
    # no extra normalization for model names; resolver must set kind='well_known'
    if typ.kind == "container" and typ.name == "list":
        inner = typ.args[0] if typ.args else TypeRef(name="Any", kind="unresolved")
        node = ast.Subscript(
            value=ast.Name(id="list"), slice=type_expr(inner), ctx=ast.Load()
        )
        return _wrap_optional(node)
    # model/error/enum or unresolved fallback
    return _wrap_optional(ast.Name(id=typ.name))


def type_has_optional(typ: TypeRef) -> bool:
    """Return True if the given TypeRef (recursively) contains an optional marker.

    For container types like list[T], checks optional flag on the container and inner T.
    """
    if getattr(typ, "optional", False):
        return True
    if typ.kind == "container" and typ.name == "list" and typ.args:
        inner = typ.args[0]
        return type_has_optional(inner)
    return False


def _gather_model_types(typ: TypeRef, acc: set[TypeRef]) -> None:
    if typ.kind == "model":
        acc.add(typ)
        return
    if typ.kind == "container" and typ.name == "list" and typ.args:
        _gather_model_types(typ.args[0], acc)


def model_types_in(typ: TypeRef) -> set[TypeRef]:
    out: set[TypeRef] = set()
    _gather_model_types(typ, out)
    return out


def _gather_wk(typ: TypeRef, acc: set[str]) -> None:
    if typ.kind == "well_known":
        acc.add(typ.name)
        return
    if typ.kind == "container" and typ.name == "list" and typ.args:
        _gather_wk(typ.args[0], acc)


def well_known_names_in(typ: TypeRef) -> set[str]:
    out: set[str] = set()
    _gather_wk(typ, out)
    return out


def _gather_enum_names(typ: TypeRef, acc: set[str]) -> None:
    if typ.kind == "enum":
        acc.add(typ.name)
        return
    if typ.kind == "container" and typ.name == "list" and typ.args:
        _gather_enum_names(typ.args[0], acc)


def enum_names_in(typ: TypeRef) -> set[str]:
    out: set[str] = set()
    _gather_enum_names(typ, out)
    return out


def emit_well_known_imports(body: list[ast.stmt], used_types: set[str]) -> None:
    modules_to_names: dict[str, set[str]] = {}
    for t in used_types:
        if t not in WELL_KNOWN_TYPES:
            continue
        import_info = get_import_info(t)
        if not import_info:
            continue
        mod_name, name = import_info
        modules_to_names.setdefault(mod_name, set()).add(name)
    for mod, names in sorted(modules_to_names.items()):
        body.append(
            ast.ImportFrom(
                module=mod, names=[ast.alias(name=n) for n in sorted(names)], level=0
            )
        )


def request_payload_name(
    service: Service, rpc: Rpc, ns_path: list[str] | None = None
) -> str:
    rpc_pascal = "".join(seg.capitalize() for seg in snake(rpc.name).split("_"))
    prefix = ns_prefix_pascal(ns_path)
    return f"{prefix}{rpc_pascal}Payload" if prefix else f"{rpc_pascal}Payload"


def response_result_name(
    service: Service, rpc: Rpc, ns_path: list[str] | None = None
) -> str:
    rpc_pascal = "".join(seg.capitalize() for seg in snake(rpc.name).split("_"))
    prefix = ns_prefix_pascal(ns_path)
    return f"{prefix}{rpc_pascal}Result" if prefix else f"{rpc_pascal}Result"


# Field metadata handling (centralized)

FIELD_KNOWN_KEYS = {
    "ge",
    "gt",
    "le",
    "lt",
    "min_length",
    "max_length",
    "pattern",
    "alias",
    "examples",
    "default",
    "default_factory",
}


def get_attr_doc(attrs: list[Attribute]) -> str | None:
    for attr in reversed(attrs):
        if attr.name == "doc":
            if attr.args:
                return str(attr.args[0])
            for key in ("value", "text", "description"):
                if key in attr.kwargs:
                    return str(attr.kwargs[key])
    return None


def field_kwargs_from_attrs(attrs: list[Attribute]) -> dict[str, object]:
    kwargs: dict[str, object] = {}
    doc = get_attr_doc(attrs)
    if doc is not None:
        kwargs["description"] = doc
    seen: set[str] = set()
    for attr in reversed(attrs):
        name = attr.name
        if name == "doc":
            continue
        if name in FIELD_KNOWN_KEYS and name not in seen:
            val: object | None = None
            if attr.args:
                val = attr.args[0]
            elif attr.kwargs and "value" in attr.kwargs:
                val = attr.kwargs["value"]
            if val is not None:
                kwargs[name] = val
                seen.add(name)
    return kwargs


def _build_field_keywords(kwargs_map: dict[str, object]) -> list[ast.keyword]:
    """Build keywords for Field(...), treating default_factory specially as an expression.

    - default: emitted as Constant
    - default_factory: if a string that looks like a dotted name or identifier, emit as Name/Attribute expr
      otherwise, fall back to Constant (to allow simple string factories, though unusual)
    Other keys: emitted as Constant.
    """
    keywords: list[ast.keyword] = []
    for key, value in kwargs_map.items():
        if key == "default_factory":
            expr: ast.expr
            if isinstance(value, str) and value:
                # build Name or dotted Attribute chain
                parts = value.split(".")
                node: ast.expr = ast.Name(id=parts[0])
                for part in parts[1:]:
                    node = ast.Attribute(value=node, attr=part)
                expr = node
            else:
                expr = ast.Constant(value=value)
            keywords.append(ast.keyword(arg=key, value=expr))
        else:
            keywords.append(ast.keyword(arg=key, value=ast.Constant(value=value)))
    return keywords


# Return annotation helper for servers
def return_annotation_expr(
    service: Service, rpc: Rpc, ns_path: list[str] | None
) -> ast.expr:
    if isinstance(rpc.returns, InlineStruct):
        return ast.Name(id=response_result_name(service, rpc, ns_path))
    if isinstance(rpc.returns, TypeRef):
        return type_expr(rpc.returns)
    return ast.Name(id="None")


def _iter_ns(ns: Namespace, prefix: list[str]) -> Iterable[tuple[list[str], object]]:
    current = prefix + [snake(ns.name)]
    for it in getattr(ns, "items", []) or []:
        if isinstance(it, (Rpc, Event)):
            yield current, it
        elif isinstance(it, Namespace):
            yield from _iter_ns(it, current)


def iter_rpcs(service: Service) -> Iterable[tuple[list[str], Rpc]]:
    for r in service.rpcs:
        yield [], r
    for ns in getattr(service, "namespaces", []) or []:
        for path, it in _iter_ns(ns, []):
            if isinstance(it, Rpc):
                yield path, it


def iter_events(service: Service) -> Iterable[tuple[list[str], Event]]:
    """Iterate over all events (both emits and listens) with namespace paths."""
    for e in getattr(service, "emits", []) or []:
        yield [], e
    for e in getattr(service, "listens", []) or []:
        yield [], e
    for ns in getattr(service, "namespaces", []) or []:
        for path, it in _iter_ns(ns, []):
            if isinstance(it, Event):
                yield path, it


def iter_emits(service: Service) -> Iterable[tuple[list[str], Event]]:
    for e in getattr(service, "emits", []) or []:
        yield [], e
    for ns in getattr(service, "namespaces", []) or []:
        for path, it in _iter_ns(ns, []):
            if isinstance(it, Event) and getattr(it, "role", None) == "emit":
                yield path, it


def iter_listens(service: Service) -> Iterable[tuple[list[str], Event]]:
    for e in getattr(service, "listens", []) or []:
        yield [], e
    for ns in getattr(service, "namespaces", []) or []:
        for path, it in _iter_ns(ns, []):
            if isinstance(it, Event) and getattr(it, "role", None) == "listen":
                yield path, it


def collect_model_types_for_service(service: Service) -> set[TypeRef]:
    names: set[TypeRef] = set()
    for _path, rpc in iter_rpcs(service):
        for p in rpc.params:
            if not is_builtin_or_well_known(p.type):
                names.add(p.type)
        if isinstance(rpc.returns, TypeRef):
            if not is_builtin_or_well_known(rpc.returns):
                names.add(rpc.returns)
        elif isinstance(rpc.returns, InlineStruct):
            for f in rpc.returns.fields:
                if not is_builtin_or_well_known(f.type):
                    names.add(f.type)
    for _path, ev in iter_events(service):
        for p in ev.params:
            if not is_builtin_or_well_known(p.type):
                names.add(p.type)
    return names


def resolve_import_module(
    module_of_service: str, target_module: str, kind: str
) -> tuple[str, int]:
    """Resolve module path and relative level for imports inside a service subpackage.

    Rules (consistent for generated files under `<pkg>/<service>/`):
    - Same service scope (target starts with `module_of_service.`):
      level = 1, module = `<rel>.<kind>` or `kind` if rel is empty
    - External service/module: level = 2, module = `<target_module>.<kind>`
    """
    if target_module.startswith(module_of_service + "."):
        rel = target_module[len(module_of_service) + 1 :]
        module = f"{rel}.{kind}" if rel else kind
        return module, 1
    module = f"{target_module}.{kind}"
    return module, 2


def subject_for_rpc(
    subject_prefix: str, service_name: str, ns_path: list[str], rpc_name: str
) -> str:
    """Generate NATS subject string for an RPC method.

    Format: {subject_prefix}.{service_snake}.rpc[.namespace_path].{rpc_snake}
    """
    service_snake = snake(service_name)
    rpc_snake = snake(rpc_name)
    ns_part = ("." + ".".join(ns_path)) if ns_path else ""
    return f"{subject_prefix}.{service_snake}.rpc{ns_part}.{rpc_snake}"


def subject_for_emit(
    subject_prefix: str, service_name: str, ns_path: list[str], event_name: str
) -> str:
    """Generate NATS subject string for an emitted event.

    Format: {subject_prefix}.{service_snake}.emit[.namespace_path].{event_snake}
    """
    service_snake = snake(service_name)
    event_snake = snake(event_name)
    ns_part = ("." + ".".join(ns_path)) if ns_path else ""
    return f"{subject_prefix}.{service_snake}.emit{ns_part}.{event_snake}"


def subject_for_listen(
    subject_prefix: str, service_name: str, ns_path: list[str], event_name: str
) -> str:
    """Generate NATS subject string for a listened event.

    Format: {subject_prefix}.{service_snake}.listen[.namespace_path].{event_snake}
    """
    service_snake = snake(service_name)
    event_snake = snake(event_name)
    ns_part = ("." + ".".join(ns_path)) if ns_path else ""
    return f"{subject_prefix}.{service_snake}.listen{ns_part}.{event_snake}"


def emit_payload_name(
    service: Service, ev: Event, ns_path: list[str] | None = None
) -> str:
    ev_pascal = "".join(seg.capitalize() for seg in snake(ev.name).split("_"))
    prefix = ns_prefix_pascal(ns_path)
    return f"{prefix}{ev_pascal}EmitEvent" if prefix else f"{ev_pascal}EmitEvent"


def listen_payload_name(
    service: Service, ev: Event, ns_path: list[str] | None = None
) -> str:
    ev_pascal = "".join(seg.capitalize() for seg in snake(ev.name).split("_"))
    prefix = ns_prefix_pascal(ns_path)
    return f"{prefix}{ev_pascal}ListenEvent" if prefix else f"{ev_pascal}ListenEvent"


def errors_const_name(ns_path: list[str], rpc_name: str) -> str:
    """Generate the name for ERRORS constant for an RPC.

    Format: ERRORS_[NS_PREFIX_]RPC_NAME
    """
    ns_prefix = ns_prefix_snake(ns_path).upper()
    rpc_upper = snake(rpc_name).upper()
    if ns_prefix:
        return f"ERRORS_{ns_prefix}_{rpc_upper}"
    return f"ERRORS_{rpc_upper}"

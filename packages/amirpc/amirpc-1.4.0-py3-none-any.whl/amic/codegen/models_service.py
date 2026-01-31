"""Service-local models (non-domain) and payload/result/event models generation (class nodes only)."""

import ast
from collections.abc import Iterable

from amic.ast.model import Event, InlineStruct, Model, Rpc, Service, TypeRef
from amic.codegen.emit import format_code
from amic.codegen.utils import (
    _build_field_keywords,
    emit_well_known_imports,
    field_kwargs_from_attrs,
    iter_emits,
    iter_events,
    iter_listens,
    iter_rpcs,
    model_types_in,
    ns_prefix_pascal,
    request_payload_name,
    response_result_name,
    type_expr,
    type_has_optional,
    well_known_names_in,
)
from amic.compilation.compiled import CompiledProject, CompiledService


def build_local_model_classes(non_domain_models: Iterable[Model]) -> list[ast.stmt]:
    classes: list[ast.stmt] = []
    # Order classes so that dependencies are defined before their users
    models = list(non_domain_models)
    name_to_model: dict[str, Model] = {m.name: m for m in models}
    # Build dependency graph: model -> set of model names it depends on
    deps: dict[str, set[str]] = {}
    for m in models:
        m_deps: set[str] = set()
        for f in m.fields:
            for t in model_types_in(f.type):
                if t.name in name_to_model and t.name != m.name:
                    m_deps.add(t.name)
        deps[m.name] = m_deps
    # Kahn's algorithm
    ordered: list[Model] = []
    no_deps = [name for name, ds in deps.items() if not ds]
    while no_deps:
        name = no_deps.pop()
        ordered.append(name_to_model[name])
        for other, other_deps in deps.items():
            if name in other_deps:
                other_deps.remove(name)
                if not other_deps:
                    no_deps.append(other)
        deps[name] = set()
    # Append remaining (cycles or isolated) preserving original order
    if len(ordered) < len(models):
        seen = {m.name for m in ordered}
        ordered.extend([m for m in models if m.name not in seen])

    for decl in ordered:
        class_body: list[ast.stmt] = []
        doc = getattr(decl, "doc", None)
        if doc:
            class_body.append(ast.Expr(value=ast.Constant(value=doc)))
        if not decl.fields:
            class_body.append(ast.Pass())
        else:
            for f in decl.fields:
                field_kwargs = field_kwargs_from_attrs(f.attrs)
                if field_kwargs:
                    kwargs = _build_field_keywords(field_kwargs)
                    field_call = ast.Call(
                        func=ast.Name(id="Field"), args=[], keywords=kwargs
                    )
                    ann = ast.Subscript(
                        value=ast.Name(id="Annotated"),
                        slice=ast.Tuple(
                            elts=[type_expr(f.type), field_call],
                            ctx=ast.Load(),
                        ),
                        ctx=ast.Load(),
                    )
                else:
                    ann = type_expr(f.type)

                # Add default value for optional fields
                default_value = (
                    ast.Constant(value=None) if type_has_optional(f.type) else None
                )

                class_body.append(
                    ast.AnnAssign(
                        target=ast.Name(id=f.name, ctx=ast.Store()),
                        annotation=ann,
                        value=default_value,
                        simple=1,
                    )
                )
        classes.append(
            ast.ClassDef(
                name=decl.name,
                bases=[ast.Name(id="AmiModel")],
                keywords=[],
                body=class_body,
                decorator_list=[],
            )
        )
    return classes


## Removed bulk builders (unused): build_request_payload_classes/build_response_result_classes/build_event_payload_classes


def build_request_payload_class(
    service: Service, rpc: Rpc, ns_path: list[str] | None
) -> ast.ClassDef:
    class_body: list[ast.stmt] = []
    doc = getattr(rpc, "doc", None)
    if doc:
        class_body.append(
            ast.Expr(
                value=ast.Constant(
                    value=f"Request payload for {service.name}.{rpc.name}: {doc}"
                )
            )
        )
    if not rpc.params:
        class_body.append(ast.Pass())
    else:
        for p in rpc.params:
            field_kwargs = field_kwargs_from_attrs(p.attrs)
            if getattr(p, "doc", None):
                first = str(p.doc).splitlines()[0]
                if first:
                    field_kwargs = dict(field_kwargs) if field_kwargs else {}
                    field_kwargs.setdefault("description", first)
            if field_kwargs:
                kwargs = _build_field_keywords(field_kwargs)
                field_call = ast.Call(
                    func=ast.Name(id="Field"), args=[], keywords=kwargs
                )
                ann = ast.Subscript(
                    value=ast.Name(id="Annotated"),
                    slice=ast.Tuple(
                        elts=[type_expr(p.type), field_call],
                        ctx=ast.Load(),
                    ),
                    ctx=ast.Load(),
                )
            else:
                ann = type_expr(p.type)

            # Add default value for optional fields
            default_value = (
                ast.Constant(value=None) if type_has_optional(p.type) else None
            )

            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id=p.name, ctx=ast.Store()),
                    annotation=ann,
                    value=default_value,
                    simple=1,
                )
            )
    return ast.ClassDef(
        name=request_payload_name(service, rpc, ns_path),
        bases=[ast.Name(id="AmiRequestPayload")],
        keywords=[],
        body=class_body,
        decorator_list=[],
    )


def build_response_result_class(
    service: Service, rpc: Rpc, ns_path: list[str] | None
) -> ast.ClassDef:
    assert isinstance(rpc.returns, InlineStruct)
    class_body: list[ast.stmt] = []
    doc = getattr(rpc, "doc", None)
    if doc:
        class_body.append(
            ast.Expr(
                value=ast.Constant(
                    value=f"Response result for {service.name}.{rpc.name}: {doc}"
                )
            )
        )
    if not rpc.returns.fields:
        class_body.append(ast.Pass())
    else:
        for f in rpc.returns.fields:
            field_kwargs = field_kwargs_from_attrs(f.attrs)
            if getattr(f, "doc", None):
                first = str(f.doc).splitlines()[0]
                if first:
                    field_kwargs = dict(field_kwargs) if field_kwargs else {}
                    field_kwargs.setdefault("description", first)
            if field_kwargs:
                kwargs = _build_field_keywords(field_kwargs)
                field_call = ast.Call(
                    func=ast.Name(id="Field"), args=[], keywords=kwargs
                )
                ann = ast.Subscript(
                    value=ast.Name(id="Annotated"),
                    slice=ast.Tuple(
                        elts=[type_expr(f.type), field_call],
                        ctx=ast.Load(),
                    ),
                    ctx=ast.Load(),
                )
            else:
                ann = type_expr(f.type)

            # Add default value for optional fields
            default_value = (
                ast.Constant(value=None) if type_has_optional(f.type) else None
            )

            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id=f.name, ctx=ast.Store()),
                    annotation=ann,
                    value=default_value,
                    simple=1,
                )
            )
    return ast.ClassDef(
        name=response_result_name(service, rpc, ns_path),
        bases=[ast.Name(id="AmiResponsePayload")],
        keywords=[],
        body=class_body,
        decorator_list=[],
    )


def build_event_payload_class(
    service: Service, ev: Event, ns_path: list[str] | None
) -> ast.ClassDef:
    class_body: list[ast.stmt] = []
    doc = getattr(ev, "doc", None)
    if doc:
        class_body.append(
            ast.Expr(
                value=ast.Constant(
                    value=f"Event payload for {service.name}.{ev.name}: {doc}"
                )
            )
        )
    if not ev.params:
        class_body.append(ast.Pass())
    else:
        for p in ev.params:
            field_kwargs = field_kwargs_from_attrs(p.attrs)
            if getattr(p, "doc", None):
                first = str(p.doc).splitlines()[0]
                if first:
                    field_kwargs = dict(field_kwargs) if field_kwargs else {}
                    field_kwargs.setdefault("description", first)
            if field_kwargs:
                kwargs = [
                    ast.keyword(arg=k, value=ast.Constant(value=v))
                    for k, v in field_kwargs.items()
                ]
                field_call = ast.Call(
                    func=ast.Name(id="Field"), args=[], keywords=kwargs
                )
                ann = ast.Subscript(
                    value=ast.Name(id="Annotated"),
                    slice=ast.Tuple(
                        elts=[type_expr(p.type), field_call],
                        ctx=ast.Load(),
                    ),
                    ctx=ast.Load(),
                )
            else:
                ann = type_expr(p.type)

            # Add default value for optional fields
            default_value = (
                ast.Constant(value=None) if type_has_optional(p.type) else None
            )

            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id=p.name, ctx=ast.Store()),
                    annotation=ann,
                    value=default_value,
                    simple=1,
                )
            )
    # Name depends on role: EmitEvent or ListenEvent
    role = getattr(ev, "role", None)
    base_name = (
        f"{ns_prefix_pascal(ns_path)}{ev.name}"
        if ns_prefix_pascal(ns_path)
        else f"{ev.name}"
    )
    if role == "emit":
        name = f"{base_name}EmitEvent"
    elif role == "listen":
        name = f"{base_name}ListenEvent"
    else:
        name = f"{base_name}Event"
    return ast.ClassDef(
        name=name,
        bases=[ast.Name(id="AmiEventPayload")],
        keywords=[],
        body=class_body,
        decorator_list=[],
    )


def build_service_models_module_ast(
    project: CompiledProject, svc: CompiledService
) -> ast.Module:
    body: list[ast.stmt] = []

    # Determine need for Annotated/Field across all RPCs (including namespaced) and events
    need_annotated = False
    for _ns_path, rpc in iter_rpcs(svc.service):
        for p in rpc.params:
            if field_kwargs_from_attrs(p.attrs) or getattr(p, "doc", None):
                need_annotated = True
                break
        if isinstance(rpc.returns, InlineStruct):
            for f in rpc.returns.fields:
                if field_kwargs_from_attrs(f.attrs) or getattr(f, "doc", None):
                    need_annotated = True
                    break
        if need_annotated:
            break
    if not need_annotated:
        for _ns_path, ev in iter_events(svc.service):
            for p in ev.params:
                if field_kwargs_from_attrs(p.attrs) or getattr(p, "doc", None):
                    need_annotated = True
                    break
            if need_annotated:
                break

    # Check if Optional[...] used anywhere (params, inline results, events, or non-domain models)
    from amic.codegen.utils import type_has_optional  # local to avoid cycles

    need_optional = False
    if any(getattr(svc, "non_domain_models", []) or []):
        for decl in getattr(svc, "non_domain_models", []) or []:
            for f in decl.fields:
                if type_has_optional(f.type):
                    need_optional = True
                    break
            if need_optional:
                break
    if not need_optional:
        for _ns_path, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if type_has_optional(p.type):
                    need_optional = True
                    break
            if need_optional:
                break
            if isinstance(rpc.returns, InlineStruct):
                for f in rpc.returns.fields:
                    if type_has_optional(f.type):
                        need_optional = True
                        break
            if need_optional:
                break
    if not need_optional:
        for _ns_path, ev in iter_events(svc.service):
            for p in ev.params:
                if type_has_optional(p.type):
                    need_optional = True
                    break
            if need_optional:
                break

    # Import pydantic Field if Annotated metadata is required
    if need_annotated:
        body.append(
            ast.ImportFrom(module="pydantic", names=[ast.alias(name="Field")], level=0)
        )
    # Import typing names as needed
    typing_names: list[ast.alias] = []
    if need_annotated:
        typing_names.append(ast.alias(name="Annotated"))
    if need_optional:
        typing_names.append(ast.alias(name="Optional"))
    if typing_names:
        body.append(ast.ImportFrom(module="typing", names=typing_names, level=0))

    # Import only used base classes from amirpc
    has_non_domain = bool(getattr(svc, "non_domain_models", []) or [])
    has_any_rpcs = any(True for _ in iter_rpcs(svc.service))
    has_inline_result = any(
        isinstance(r.returns, InlineStruct) for _p, r in iter_rpcs(svc.service)
    )
    has_events = any(True for _ in iter_events(svc.service))
    amirpc_names: list[ast.alias] = []
    if has_non_domain:
        amirpc_names.append(ast.alias(name="AmiModel"))
    if has_any_rpcs:
        amirpc_names.append(ast.alias(name="AmiRequestPayload"))
    if has_inline_result:
        amirpc_names.append(ast.alias(name="AmiResponsePayload"))
    if has_events:
        amirpc_names.append(ast.alias(name="AmiEventPayload"))
    if amirpc_names:
        body.append(ast.ImportFrom(module="amirpc", names=amirpc_names, level=0))

    # Well-known imports used anywhere in models + enum imports
    used_wk: set[str] = set()
    used_enums: set[str] = set()
    for decl in getattr(svc, "non_domain_models", []) or []:
        for f in decl.fields:
            if isinstance(f.type, TypeRef):
                used_wk.update(well_known_names_in(f.type))
                from amic.codegen.utils import (
                    enum_names_in,  # local import to avoid cycle
                )

                used_enums.update(enum_names_in(f.type))
    for _ns_path, rpc in iter_rpcs(svc.service):
        for p in rpc.params:
            if isinstance(p.type, TypeRef):
                used_wk.update(well_known_names_in(p.type))
                from amic.codegen.utils import enum_names_in

                used_enums.update(enum_names_in(p.type))
        if isinstance(rpc.returns, InlineStruct):
            for f in rpc.returns.fields:
                if isinstance(f.type, TypeRef):
                    used_wk.update(well_known_names_in(f.type))
                    from amic.codegen.utils import enum_names_in

                    used_enums.update(enum_names_in(f.type))
    for _ns_path, ev in iter_events(svc.service):
        for p in ev.params:
            if isinstance(p.type, TypeRef):
                used_wk.update(well_known_names_in(p.type))
                from amic.codegen.utils import enum_names_in

                used_enums.update(enum_names_in(p.type))
    if used_wk:
        emit_well_known_imports(body, used_wk)
    if used_enums:
        # Prefer local service enums (level=1), fall back to domain enums (level=2)
        local_enum_names = {e.name for e in (getattr(svc, "local_enums", []) or [])}
        domain_enum_names = {
            e.name for e in (getattr(project, "domain_enums", []) or [])
        }
        to_import_local = sorted(used_enums & local_enum_names)
        to_import_domain = sorted(
            (used_enums - set(local_enum_names)) & domain_enum_names
        )
        if to_import_local:
            body.append(
                ast.ImportFrom(
                    module="enums",
                    names=[ast.alias(name=n) for n in to_import_local],
                    level=1,
                )
            )
        if to_import_domain:
            body.append(
                ast.ImportFrom(
                    module="enums",
                    names=[ast.alias(name=n) for n in to_import_domain],
                    level=2,
                )
            )

    # Collect domain model references used in RPC params/returns and non-domain models
    used_models: set[str] = set()
    for decl in getattr(svc, "non_domain_models", []) or []:
        for f in decl.fields:
            if isinstance(f.type, TypeRef):
                for model_ref in model_types_in(f.type):
                    if model_ref.kind == "model":
                        used_models.add(model_ref.name)
    for _ns_path, rpc in iter_rpcs(svc.service):
        for p in rpc.params:
            if isinstance(p.type, TypeRef):
                for model_ref in model_types_in(p.type):
                    if model_ref.kind == "model":
                        used_models.add(model_ref.name)
        if isinstance(rpc.returns, InlineStruct):
            for f in rpc.returns.fields:
                if isinstance(f.type, TypeRef):
                    for model_ref in model_types_in(f.type):
                        if model_ref.kind == "model":
                            used_models.add(model_ref.name)
    for _ns_path, ev in iter_events(svc.service):
        for p in ev.params:
            if isinstance(p.type, TypeRef):
                for model_ref in model_types_in(p.type):
                    if model_ref.kind == "model":
                        used_models.add(model_ref.name)

    # Import domain models from ..models
    domain_model_names = {m.name for m in (getattr(project, "domain_models", []) or [])}
    to_import_domain_models = sorted(used_models & domain_model_names)
    if to_import_domain_models:
        body.append(
            ast.ImportFrom(
                module="models",
                names=[ast.alias(name=n) for n in to_import_domain_models],
                level=2,
            )
        )

    # Local service models (non-domain)
    # Build local non-domain models (if any)
    body.extend(build_local_model_classes(getattr(svc, "non_domain_models", []) or []))

    # Request payload, response result and event payload classes
    for ns_path, rpc in iter_rpcs(svc.service):
        body.append(build_request_payload_class(svc.service, rpc, ns_path))
    for ns_path, rpc in iter_rpcs(svc.service):
        if isinstance(rpc.returns, InlineStruct):
            body.append(build_response_result_class(svc.service, rpc, ns_path))
    # Emit and Listen payloads
    for ns_path, ev in iter_emits(svc.service):
        body.append(build_event_payload_class(svc.service, ev, ns_path))
    for ns_path, ev in iter_listens(svc.service):
        body.append(build_event_payload_class(svc.service, ev, ns_path))

    return ast.Module(body=body, type_ignores=[])


def render_service_models_module(project: CompiledProject, svc: CompiledService) -> str:
    mod = ast.fix_missing_locations(build_service_models_module_ast(project, svc))
    return format_code(ast.unparse(mod))

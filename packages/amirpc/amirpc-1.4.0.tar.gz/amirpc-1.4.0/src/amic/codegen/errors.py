"""Errors code generation (domain and service-local)."""

import ast
from collections.abc import Iterable

from amic.ast.model import ErrorDecl, Model, TypeRef
from amic.codegen.emit import format_code
from amic.codegen.utils import (
    emit_well_known_imports,
    get_attr_doc,
    py_type,
    resolve_import_module,
    well_known_names_in,
)
from amic.compilation.compiled import CompiledProject, CompiledService


def build_domain_errors_ast(
    errors: Iterable[ErrorDecl], domain_models: set[str]
) -> ast.Module:
    body: list[ast.stmt] = []
    errs = list(errors)
    if not errs:
        # Always provide an ERRORS registry, even if empty
        body.append(
            ast.Assign(
                targets=[ast.Name(id="ERRORS")], value=ast.Dict(keys=[], values=[])
            )
        )
        return ast.Module(body=body, type_ignores=[])
    body.append(
        ast.ImportFrom(
            module="amirpc", names=[ast.alias(name="AmiServiceError")], level=0
        )
    )
    body.append(
        ast.ImportFrom(module="typing", names=[ast.alias(name="Optional")], level=0)
    )
    # Well-known type imports used in error parameters (e.g., UUID)
    wk_used: set[str] = set()
    for e in errs:
        for p in e.params:
            wk_used.update(well_known_names_in(p.type))
    if wk_used:
        emit_well_known_imports(body, wk_used)
    need_models: set[str] = set()
    for e in errs:
        for p in e.params:
            if isinstance(p.type, TypeRef) and p.type.kind not in {
                "builtin",
                "well_known",
            }:
                need_models.add(p.type.name)
    if need_models:
        body.append(
            ast.ImportFrom(
                module=".models",
                names=[ast.alias(name=n) for n in sorted(need_models)],
                level=1,
            )
        )
    for e in errors:
        class_body: list[ast.stmt] = []
        # Docstring: prefer ASL doc-comment, fallback to [doc: "..."] attribute
        doc = getattr(e, "doc", None) or get_attr_doc(getattr(e, "attrs", []))
        if doc:
            class_body.append(ast.Expr(value=ast.Constant(value=doc)))
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id="code", ctx=ast.Store()),
                annotation=ast.Name(id="str"),
                value=ast.Constant(
                    value="".join(
                        [("_" + c.lower()) if c.isupper() else c for c in e.name]
                    ).lstrip("_")
                ),
                simple=1,
            )
        )
        for p in e.params:
            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id=p.name, ctx=ast.Store()),
                    annotation=ast.Name(id=py_type(p.type)),
                    value=None,
                    simple=1,
                )
            )
        # Defaults from attributes if provided
        http_status = None
        default_message = None
        for a in getattr(e, "attrs", []):
            if a.name == "http_status" and a.args:
                http_status = a.args[0]
            if a.name == "message" and a.args:
                default_message = a.args[0]
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id="http_status", ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name(id="Optional"),
                    slice=ast.Name(id="int"),
                    ctx=ast.Load(),
                ),
                value=(
                    ast.Constant(value=http_status)
                    if http_status is not None
                    else ast.Constant(value=None)
                ),
                simple=1,
            )
        )
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id="default_message", ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name(id="Optional"),
                    slice=ast.Name(id="str"),
                    ctx=ast.Load(),
                ),
                value=(
                    ast.Constant(value=default_message)
                    if default_message is not None
                    else ast.Constant(value=None)
                ),
                simple=1,
            )
        )
        body.append(
            ast.ClassDef(
                name=e.name,
                bases=[ast.Name(id="AmiServiceError")],
                keywords=[],
                body=class_body,
                decorator_list=[],
            )
        )
    # Build ERRORS registry mapping code -> class
    if errs:
        dict_keys: list[ast.expr] = []
        dict_values: list[ast.expr] = []
        for e in errs:
            code_snake = "".join(
                [("_" + c.lower()) if c.isupper() else c for c in e.name]
            ).lstrip("_")
            dict_keys.append(ast.Constant(value=code_snake))
            dict_values.append(ast.Name(id=e.name))
        body.append(
            ast.Assign(
                targets=[ast.Name(id="ERRORS")],
                value=ast.Dict(keys=dict_keys, values=dict_values),
            )
        )
    return ast.Module(body=body, type_ignores=[])


def render_domain_errors(
    errors: Iterable[ErrorDecl], domain_models: Iterable[Model]
) -> str:
    names = {m.name for m in domain_models}
    return format_code(
        ast.unparse(ast.fix_missing_locations(build_domain_errors_ast(errors, names)))
    )


def build_service_errors_ast(
    project: CompiledProject, svc: CompiledService
) -> ast.Module:
    body: list[ast.stmt] = []
    errs = list(svc.local_errors)
    # Also include errors declared in other files within the same service module (e.g., ./errors.asl)
    same_module_errs = (
        svc.dep_error_modules.get(svc.module, [])
        if getattr(svc, "dep_error_modules", None)
        else []
    )
    if same_module_errs:
        errs.extend(same_module_errs)
    if not errs:
        # Always provide an ERRORS registry, even if empty
        body.append(
            ast.Assign(
                targets=[ast.Name(id="ERRORS")], value=ast.Dict(keys=[], values=[])
            )
        )
        return ast.Module(body=body, type_ignores=[])
    body.append(
        ast.ImportFrom(
            module="amirpc", names=[ast.alias(name="AmiServiceError")], level=0
        )
    )
    body.append(
        ast.ImportFrom(module="typing", names=[ast.alias(name="Optional")], level=0)
    )

    # Well-known type imports used in error parameters (e.g., UUID)
    wk_used: set[str] = set()
    for err in errs:
        for p in err.params:
            wk_used.update(well_known_names_in(p.type))
    if wk_used:
        emit_well_known_imports(body, wk_used)

    local_model_names = {m.name for m in svc.local_models}
    domain_names = {m.name for m in project.domain_models}
    need_local: set[str] = set()
    need_domain: set[str] = set()
    external_needed_by_module: dict[str, list[str]] = {}

    for err in errs:
        for p in err.params:
            if not isinstance(p.type, TypeRef) or p.type.kind in {
                "builtin",
                "well_known",
            }:
                continue
            if p.type.name in local_model_names:
                need_local.add(p.type.name)
            else:
                mod = svc.imported_model_modules.get(p.type.name)
                if mod == "__DOMAIN__":
                    if p.type.name in domain_names:
                        need_domain.add(p.type.name)
                elif mod:
                    external_needed_by_module.setdefault(mod, []).append(p.type.name)

    if need_local:
        body.append(
            ast.ImportFrom(
                module=".models",
                names=[ast.alias(name=n) for n in sorted(need_local)],
                level=1,
            )
        )
    if need_domain:
        body.append(
            ast.ImportFrom(
                module="models",
                names=[ast.alias(name=n) for n in sorted(need_domain)],
                level=2,
            )
        )
    for mod_path, names in sorted(external_needed_by_module.items()):
        if mod_path == "__DOMAIN__":
            module_name, level = ("models", 2)
        else:
            module_name, level = resolve_import_module(svc.module, mod_path, "models")
        body.append(
            ast.ImportFrom(
                module=module_name,
                names=[ast.alias(name=n) for n in sorted(set(names))],
                level=level,
            )
        )

    # Generate classes for both locally-declared and same-module imported errors
    for err in errs:
        class_body: list[ast.stmt] = []
        # Docstring: prefer ASL doc-comment, fallback to [doc: "..."] attribute
        doc = getattr(err, "doc", None) or get_attr_doc(getattr(err, "attrs", []))
        if doc:
            class_body.append(ast.Expr(value=ast.Constant(value=doc)))

        code_snake = "".join(
            [("_" + c.lower()) if c.isupper() else c for c in err.name]
        ).lstrip("_")
        svc_name = "".join(
            [("_" + c.lower()) if c.isupper() else c for c in svc.name]
        ).lstrip("_")
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id="code", ctx=ast.Store()),
                annotation=ast.Name(id="str"),
                value=ast.Constant(value=f"{svc_name}.{code_snake}"),
                simple=1,
            )
        )

        for p in err.params:
            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id=p.name, ctx=ast.Store()),
                    annotation=ast.Name(id=py_type(p.type)),
                    value=None,
                    simple=1,
                )
            )

        http_status = None
        default_message = None
        for a in err.attrs:
            if a.name == "http_status" and a.args:
                http_status = a.args[0]
            if a.name == "message" and a.args:
                default_message = a.args[0]
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id="http_status", ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name(id="Optional"),
                    slice=ast.Name(id="int"),
                    ctx=ast.Load(),
                ),
                value=(
                    ast.Constant(value=http_status)
                    if http_status is not None
                    else ast.Constant(value=None)
                ),
                simple=1,
            )
        )
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id="default_message", ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name(id="Optional"),
                    slice=ast.Name(id="str"),
                    ctx=ast.Load(),
                ),
                value=(
                    ast.Constant(value=default_message)
                    if default_message is not None
                    else ast.Constant(value=None)
                ),
                simple=1,
            )
        )
        body.append(
            ast.ClassDef(
                name=err.name,
                bases=[ast.Name(id="AmiServiceError")],
                keywords=[],
                body=class_body,
                decorator_list=[],
            )
        )
    # Build ERRORS registry mapping code -> class
    if errs:
        dict_keys: list[ast.expr] = []
        dict_values: list[ast.expr] = []
        for err in errs:
            code_snake = "".join(
                [("_" + c.lower()) if c.isupper() else c for c in err.name]
            ).lstrip("_")
            svc_name = "".join(
                [("_" + c.lower()) if c.isupper() else c for c in svc.name]
            ).lstrip("_")
            full_code = f"{svc_name}.{code_snake}"
            dict_keys.append(ast.Constant(value=full_code))
            dict_values.append(ast.Name(id=err.name))
        body.append(
            ast.Assign(
                targets=[ast.Name(id="ERRORS")],
                value=ast.Dict(keys=dict_keys, values=dict_values),
            )
        )

    return ast.Module(body=body, type_ignores=[])


def render_service_errors(project: CompiledProject, svc: CompiledService) -> str:
    mod = ast.fix_missing_locations(build_service_errors_ast(project, svc))
    return format_code(ast.unparse(mod))

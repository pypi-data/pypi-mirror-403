"""Models code generation (domain and service-local)."""

import ast
from collections.abc import Iterable

from amic.ast.model import Model, TypeRef
from amic.codegen.emit import format_code
from amic.codegen.utils import (
    _build_field_keywords,
    emit_well_known_imports,
    enum_names_in,
    field_kwargs_from_attrs,
    type_expr,
    type_has_optional,
    well_known_names_in,
)


def build_domain_models_ast(models: Iterable[Model]) -> ast.Module:
    body: list[ast.stmt] = []
    need_annotated = any(
        field_kwargs_from_attrs(f.attrs) or bool(getattr(f, "doc", None))
        for m in models
        if getattr(m, "domain", False)
        for f in m.fields
    )
    # Determine if Optional[...] appears anywhere in domain models
    need_optional = any(
        type_has_optional(f.type)
        for m in models
        if getattr(m, "domain", False)
        for f in m.fields
    )
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
    body.append(
        ast.ImportFrom(module="amirpc", names=[ast.alias(name="AmiModel")], level=0)
    )

    used_wk: set[str] = set()
    used_enums: set[str] = set()
    for decl in models:
        if getattr(decl, "domain", False):
            for f in decl.fields:
                if isinstance(f.type, TypeRef):
                    used_wk.update(well_known_names_in(f.type))
                    used_enums.update(enum_names_in(f.type))
    if used_wk:
        emit_well_known_imports(body, used_wk)
    if used_enums:
        body.append(
            ast.ImportFrom(
                module="enums",
                names=[ast.alias(name=n) for n in sorted(used_enums)],
                level=1,
            )
        )

    # Import enums if referenced by any domain model field
    # We rely on Python name resolution: domain enums are emitted into sibling module 'enums'
    # Importing is not strictly necessary at class body level since annotations can reference names
    # available in the same package when imported by user. We skip explicit import here to avoid
    # ordering issues; users should import from package root as needed.

    for decl in models:
        if not getattr(decl, "domain", False):
            continue
        class_body: list[ast.stmt] = []
        doc = getattr(decl, "doc", None)
        if doc:
            class_body.append(ast.Expr(value=ast.Constant(value=doc)))
        if not decl.fields:
            class_body.append(ast.Pass())
        else:
            for f in decl.fields:
                field_kwargs = field_kwargs_from_attrs(f.attrs)
                # Ensure description from doc first line if present
                doc_first: str | None = None
                if getattr(f, "doc", None):
                    doc_first = str(f.doc).splitlines()[0]
                    if doc_first:
                        field_kwargs = dict(field_kwargs) if field_kwargs else {}
                        field_kwargs.setdefault("description", doc_first)
                if field_kwargs:
                    kwargs = _build_field_keywords(field_kwargs)
                    field_call = ast.Call(
                        func=ast.Name(id="Field"), args=[], keywords=kwargs
                    )
                    ann = ast.Subscript(
                        value=ast.Name(id="Annotated"),
                        slice=ast.Tuple(
                            elts=[type_expr(f.type), field_call], ctx=ast.Load()
                        ),
                        ctx=ast.Load(),
                    )
                else:
                    ann = type_expr(f.type)
                # Note: Python AST has no comment nodes; we only set Field(description) using first line.
                # Full doc text is preserved in the ASL and can be used by external tools if needed.

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
        body.append(
            ast.ClassDef(
                name=decl.name,
                bases=[ast.Name(id="AmiModel")],
                keywords=[],
                body=class_body,
                decorator_list=[],
            )
        )
    return ast.Module(body=body, type_ignores=[])


def render_domain_models(models: Iterable[Model]) -> str:
    return format_code(
        ast.unparse(ast.fix_missing_locations(build_domain_models_ast(models)))
    )

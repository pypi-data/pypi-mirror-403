"""Enum code generation for domain-level enums.

Generates Python Enum classes based on ASL enum declarations.
"""

import ast
from collections.abc import Iterable

from amic.ast.model import EnumDecl, EnumMember
from amic.codegen.emit import format_code


def _enum_member_value(
    base: str, member: EnumMember, next_int: int
) -> tuple[ast.expr, int]:
    """Compute AST value for an enum member and return the next int counter.

    Rules:
    - string base: if value is None -> lower(member.name)
    - int base: if value is None -> next_int (auto-increment from 0)
    """
    if base == "string":
        if isinstance(member.value, str):
            return ast.Constant(value=member.value), next_int
        # Default: lower-case of the identifier name
        return ast.Constant(value=member.name.lower()), next_int
    # int base
    if isinstance(member.value, int):
        return ast.Constant(value=int(member.value)), int(member.value) + 1
    return ast.Constant(value=next_int), next_int + 1


def build_domain_enums_ast(enums: Iterable[EnumDecl]) -> ast.Module:
    body: list[ast.stmt] = []
    enums_list = [e for e in enums]
    if not enums_list:
        return ast.Module(body=body, type_ignores=[])

    # Import required Enum base classes
    need_str = any(e.base == "string" for e in enums_list)
    need_int = any(e.base == "int" for e in enums_list)
    names: list[ast.alias] = []
    if need_str:
        names.append(ast.alias(name="StrEnum"))
    if need_int:
        names.append(ast.alias(name="IntEnum"))
    if names:
        body.append(ast.ImportFrom(module="enum", names=names, level=0))

    for decl in enums_list:
        class_body: list[ast.stmt] = []
        if getattr(decl, "doc", None):
            class_body.append(ast.Expr(value=ast.Constant(value=str(decl.doc))))
        next_int: int = 0
        for mem in decl.members:
            val_node, next_int = _enum_member_value(decl.base, mem, next_int)
            class_body.append(
                ast.Assign(targets=[ast.Name(id=mem.name)], value=val_node)
            )
        base_name = "StrEnum" if decl.base == "string" else "IntEnum"
        body.append(
            ast.ClassDef(
                name=decl.name,
                bases=[ast.Name(id=base_name)],
                keywords=[],
                body=class_body if class_body else [ast.Pass()],
                decorator_list=[],
            )
        )
    return ast.Module(body=body, type_ignores=[])


def render_domain_enums(enums: Iterable[EnumDecl]) -> str:
    enums_list = list(enums)
    if not enums_list:
        return ""
    module = ast.fix_missing_locations(build_domain_enums_ast(enums_list))
    return format_code(ast.unparse(module))


def render_service_enums(enums: Iterable[EnumDecl]) -> str:
    # Reuse the same builder: service enums have identical codegen
    return render_domain_enums(enums)

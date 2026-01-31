"""Helpers to build import AST nodes for generated modules."""

import ast
from collections.abc import Iterable


def import_from(module: str, names: Iterable[str], level: int = 0) -> ast.ImportFrom:
    return ast.ImportFrom(
        module=module, names=[ast.alias(name=n) for n in names], level=level
    )

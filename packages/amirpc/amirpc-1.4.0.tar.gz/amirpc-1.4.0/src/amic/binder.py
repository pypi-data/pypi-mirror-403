from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from amic.ast.model import EnumDecl, ErrorDecl, Model, ModuleFile, Namespace, Service
from amic.compilation.compiled import (
    WELL_KNOWN_ERRORS,
    WELL_KNOWN_NAMESPACE,
    WELL_KNOWN_TYPES,
)
from amic.errors import AmiToolCompileError as AmiCompileError
from amic.locate import loc_ref_line, locate_header_line
from amic.modules import collect_module


@dataclass(frozen=True)
class Symbol:
    id: str
    name: str
    kind: str  # model | error | service | namespace | builtin | well_known
    namespace: str | None = None
    absolute_id: str | None = None
    is_domain: bool = False
    exported: bool = True
    node: object | None = None


@dataclass
class Binding:
    kind: str  # decl | import | alias
    target: Symbol
    from_scope: str | None = None
    alias: str | None = None


@dataclass
class Scope:
    id: str
    kind: str  # prelude | module | service | namespace
    parent: Optional["Scope"]
    bindings: dict[str, Binding]


@dataclass
class BoundModule:
    scope: Scope
    exports: dict[str, Symbol]
    unit_path: Path


def _make_prelude_scope() -> Scope:
    scope = Scope(id="scope:prelude", kind="prelude", parent=None, bindings={})
    for name in ("int", "string", "bool", "float"):
        sym = Symbol(id=f"sym:builtin:{name}", name=name, kind="builtin", exported=True)
        scope.bindings[name] = Binding(kind="decl", target=sym)
    return scope


def _make_well_known_scope(parent: Scope) -> BoundModule:
    wk_scope = Scope(
        id=f"scope:{WELL_KNOWN_NAMESPACE}", kind="module", parent=parent, bindings={}
    )
    exports: dict[str, Symbol] = {}
    # Add well-known types (models)
    for name in WELL_KNOWN_TYPES:
        sym = Symbol(
            id=f"sym:{WELL_KNOWN_NAMESPACE}:{name}",
            name=name,
            kind="well_known",
            namespace=WELL_KNOWN_NAMESPACE,
            absolute_id=f"{WELL_KNOWN_NAMESPACE}:{name}",
            exported=True,
        )
        exports[name] = sym
    # Add well-known errors
    for name in WELL_KNOWN_ERRORS:
        sym = Symbol(
            id=f"sym:{WELL_KNOWN_NAMESPACE}:{name}",
            name=name,
            kind="error",  # errors have kind="error", not "well_known"
            namespace=WELL_KNOWN_NAMESPACE,
            absolute_id=f"{WELL_KNOWN_NAMESPACE}:{name}",
            exported=True,
        )
        exports[name] = sym
    # note: не публікуємо їх у prelude автоматично; доступ лише через import → биндинг у модульному scope
    return BoundModule(
        scope=wk_scope, exports=exports, unit_path=Path(f"<{WELL_KNOWN_NAMESPACE}>")
    )


class BinderCache:
    def __init__(self, prelude: Scope, well_known: BoundModule):
        self.prelude = prelude
        self.well_known = well_known
        self.modules: dict[Path, BoundModule] = {}
        # Track modules currently being bound to detect cycles
        self._in_progress_stack: list[Path] = []
        self._in_progress_set: set[Path] = set()


def bind_module(
    root_dir: Path, current_file: Path, unit: ModuleFile, cache: BinderCache
) -> BoundModule:
    # Detect direct self-reentry
    if current_file in cache._in_progress_set:
        # Build a readable cycle from the stack
        try:
            start = cache._in_progress_stack.index(current_file)
            cycle = cache._in_progress_stack[start:] + [current_file]
        except ValueError:
            cycle = [current_file]
        chain = " -> ".join(str(p) for p in cycle)
        raise AmiCompileError(
            f"Cyclic import detected: {chain}",
            file=current_file,
            stage="bind",
            hint="Break the cycle by extracting shared types to a separate module or re-structuring imports",
        )

    cache._in_progress_stack.append(current_file)
    cache._in_progress_set.add(current_file)

    scope = Scope(
        id=f"scope:{(unit.module or '<unnamed>')}@{current_file}",
        kind="module",
        parent=cache.prelude,
        bindings={},
    )
    exports: dict[str, Symbol] = {}

    ns = unit.module
    # 1) Imports → import bindings (must not shadow existing names)
    for imp in unit.imports:
        # special case: well-known virtual module
        if imp.module == "@/well-known":
            target = cache.well_known
        else:
            sub = collect_module(root_dir, current_file, imp.module)
            # Cycle check BEFORE recursing
            if sub.path in cache._in_progress_set:
                # Construct cycle chain ending at sub.path
                stack = cache._in_progress_stack
                try:
                    start = stack.index(sub.path)
                    cycle_paths = stack[start:] + [sub.path]
                except ValueError:
                    cycle_paths = [sub.path]
                chain = " -> ".join(str(p) for p in cycle_paths)
                raise AmiCompileError(
                    f"Cyclic import detected: {chain}",
                    file=current_file,
                    line=loc_ref_line(current_file, imp.module),
                    stage="bind",
                    hint=(
                        "Cyclic imports are forbidden. Extract shared declarations to a common module, "
                        "or remove the back-reference."
                    ),
                )
            if sub.path not in cache.modules:
                cache.modules[sub.path] = bind_module(
                    root_dir, sub.path, sub.ast, cache
                )
            target = cache.modules[sub.path]

        for item in imp.items:
            if item.kind == "service":
                # services імпортуємо лише для infrastructure, тут можемо пропускати або забороняти
                continue
            name = item.alias or item.name
            if item.name not in target.exports:
                raise AmiCompileError(
                    f"Imported name '{item.name}' not found in module",
                    file=current_file,
                    line=loc_ref_line(current_file, imp.module),
                    stage="bind",
                )
            sym = target.exports[item.name]
            # filter by kind match when available
            # Allow importing well-known types via `model` keyword
            if item.kind in {"model", "error", "enum"}:
                allowed_kinds = {item.kind}
                if item.kind == "model":
                    allowed_kinds = {"model", "well_known"}
                if sym.kind not in allowed_kinds:
                    raise AmiCompileError(
                        f"Imported {item.kind} '{item.name}' is not a {item.kind} in the target module",
                        file=current_file,
                        line=loc_ref_line(current_file, imp.module),
                        stage="bind",
                    )
            if name in scope.bindings:
                # ambiguous/shadowing
                raise AmiCompileError(
                    f"Name '{name}' is already defined (shadowing/ambiguous import)",
                    file=current_file,
                    line=loc_ref_line(current_file, imp.module),
                    stage="bind",
                    hint="Use alias to disambiguate",
                )
            scope.bindings[name] = Binding(
                kind="import", target=sym, from_scope=target.scope.id, alias=item.alias
            )

    # 2) Local declarations → symbols and decl bindings (must not shadow existing names)
    for d in unit.decls:
        if isinstance(d, Model):
            if d.name in scope.bindings:
                raise AmiCompileError(
                    f"Name '{d.name}' is already defined (shadowing/ambiguous import)",
                    file=current_file,
                    line=locate_header_line(current_file, d),
                    stage="bind",
                    hint="Use alias or rename the symbol",
                )
            sym = Symbol(
                id=f"sym:{ns}:{d.name}",
                name=d.name,
                kind="model",
                namespace=ns,
                absolute_id=f"{ns}:{d.name}" if ns else d.name,
                is_domain=getattr(d, "domain", False),
                exported=True,
                node=d,
            )
            exports[d.name] = sym
            scope.bindings[d.name] = Binding(kind="decl", target=sym)
        elif isinstance(d, ErrorDecl):
            if d.name in scope.bindings:
                raise AmiCompileError(
                    f"Name '{d.name}' is already defined (shadowing/ambiguous import)",
                    file=current_file,
                    line=locate_header_line(current_file, d),
                    stage="bind",
                    hint="Use alias or rename the symbol",
                )
            sym = Symbol(
                id=f"sym:{ns}:{d.name}",
                name=d.name,
                kind="error",
                namespace=ns,
                absolute_id=f"{ns}:{d.name}" if ns else d.name,
                is_domain=getattr(d, "domain", False),
                exported=True,
                node=d,
            )
            exports[d.name] = sym
            scope.bindings[d.name] = Binding(kind="decl", target=sym)
        elif isinstance(d, Service):
            if d.name in scope.bindings:
                raise AmiCompileError(
                    f"Name '{d.name}' is already defined (shadowing/ambiguous import)",
                    file=current_file,
                    line=locate_header_line(current_file, d),
                    stage="bind",
                    hint="Use alias or rename the symbol",
                )
            sym = Symbol(
                id=f"sym:{ns}:{d.name}",
                name=d.name,
                kind="service",
                namespace=ns,
                absolute_id=f"{ns}:{d.name}" if ns else d.name,
                exported=True,
                node=d,
            )
            exports[d.name] = sym
            scope.bindings[d.name] = Binding(kind="decl", target=sym)
        elif isinstance(d, Namespace):
            if d.name in scope.bindings:
                raise AmiCompileError(
                    f"Name '{d.name}' is already defined (shadowing/ambiguous import)",
                    file=current_file,
                    line=locate_header_line(current_file, d),
                    stage="bind",
                    hint="Use alias or rename the symbol",
                )
            sym = Symbol(
                id=f"sym:{ns}:{d.name}",
                name=d.name,
                kind="namespace",
                namespace=ns,
                absolute_id=f"{ns}:{d.name}" if ns else d.name,
                exported=True,
                node=d,
            )
            exports[d.name] = sym
            scope.bindings[d.name] = Binding(kind="decl", target=sym)
        elif isinstance(d, EnumDecl):
            if d.name in scope.bindings:
                raise AmiCompileError(
                    f"Name '{d.name}' is already defined (shadowing/ambiguous import)",
                    file=current_file,
                    line=locate_header_line(current_file, d),
                    stage="bind",
                    hint="Use alias or rename the symbol",
                )
            sym = Symbol(
                id=f"sym:{ns}:{d.name}",
                name=d.name,
                kind="enum",
                namespace=ns,
                absolute_id=f"{ns}:{d.name}" if ns else d.name,
                is_domain=getattr(d, "domain", False),
                exported=True,
                node=d,
            )
            exports[d.name] = sym
            scope.bindings[d.name] = Binding(kind="decl", target=sym)

    bound = BoundModule(scope=scope, exports=exports, unit_path=current_file)
    # Mark current module as finished
    cache._in_progress_stack.pop()
    cache._in_progress_set.discard(current_file)
    return bound


def make_project_binder() -> BinderCache:
    prelude = _make_prelude_scope()
    well_known = _make_well_known_scope(prelude)
    return BinderCache(prelude=prelude, well_known=well_known)

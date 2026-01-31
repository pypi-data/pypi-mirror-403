from pathlib import Path

from amic.ast.model import (
    ErrorDecl,
    Event,
    InlineStruct,
    Model,
    ModuleFile,
    Namespace,
    Rpc,
    Service,
    TypeRef,
)
from amic.binder import BinderCache, Symbol, bind_module
from amic.compilation.compiled import (
    WELL_KNOWN_ERRORS,
    WELL_KNOWN_NAMESPACE,
    WELL_KNOWN_TYPES,
)
from amic.decorators import apply_decorators_parsed
from amic.errors import AmiToolCompileError as AmiCompileError
from amic.locate import (
    loc_ref_line,
    loc_type_usage_line,
)
from amic.modules import ModuleUnit
from amic.parsing.parser import parse_file as parse_one


def resolve_path(root_dir: Path, current_file: Path, ref: str) -> Path:
    if ref.startswith("$/"):
        return (root_dir / ref[2:]).resolve()
    p = Path(ref)
    if p.is_absolute():
        return p
    return (current_file.parent / p).resolve()


def ns_for_file(root_dir: Path, file_path: Path) -> str:
    rel = file_path.relative_to(root_dir)
    if file_path.name == "mod.asl":
        ns_parts = list(rel.parent.parts)
    else:
        ns_parts = list(rel.with_suffix("").parts)
    return ".".join(ns_parts) if ns_parts else ""


## Use ModuleUnit from amic.modules to avoid redefinition


def make_well_known_module() -> ModuleUnit:
    # Provide a virtual module with well-known model and error names
    decls: list[object] = []
    # Add well-known types (models)
    for name in WELL_KNOWN_TYPES:
        decls.append(
            Model(name=name, fields=[], attrs=[], domain=False, decorators=None)
        )
    # Add well-known errors
    for name in WELL_KNOWN_ERRORS:
        decls.append(
            ErrorDecl(name=name, params=[], attrs=[], domain=False, decorators=None)
        )
    ast = ModuleFile(imports=[], decls=decls, module=WELL_KNOWN_NAMESPACE)
    pseudo_path = Path(f"<{WELL_KNOWN_NAMESPACE}>")
    return ModuleUnit(ns=WELL_KNOWN_NAMESPACE, path=pseudo_path, ast=ast)


def collect_module(root_dir: Path, current_file: Path, ref: str) -> ModuleUnit:
    if ref.startswith("@/"):
        if ref == "@/well-known":
            return make_well_known_module()
        raise AmiCompileError(
            f"Unknown virtual module provider: {ref}",
            file=current_file,
            line=loc_ref_line(current_file, ref),
            stage="resolve",
            hint="Only '@/well-known' is supported at the moment",
        )
    path = resolve_path(root_dir, current_file, ref)
    if not path.exists():
        raise AmiCompileError(
            f"Module file not found: {ref}",
            file=current_file,
            line=loc_ref_line(current_file, ref),
            column=None,
            stage="resolve",
            hint="Check the path in 'services{ X from \"...\" };' or file existence",
        )
    ast = parse_one(path)
    # apply decorators to submodule
    apply_decorators_parsed(ast, file=path)
    if not isinstance(ast, ModuleFile):
        if hasattr(ast, "infrastructure"):
            raise AmiCompileError(
                "Only one infrastructure is allowed in an imported file",
                file=path,
                stage="resolve",
                hint="Move 'infrastructure' to the root file and import modules without it",
            )
        raise AmiCompileError(
            "Module must be a module file",
            file=path,
            stage="resolve",
            hint="The file must contain type/service declarations and, if needed, 'module \"...\"';",
        )
    ns = ast.module or ns_for_file(root_dir, path)
    return ModuleUnit(ns=ns, path=path, ast=ast)


def resolve_types_in_module(
    unit: ModuleUnit, *, binder: BinderCache, root_dir: Path
) -> None:
    # Bind current module to get its scope and imports
    bound = bind_module(
        root_dir=root_dir, current_file=unit.path, unit=unit.ast, cache=binder
    )

    # Build lookup: name -> Symbol for all visible type-like bindings (models, enums, well-known)
    visible_types: dict[str, Symbol] = {}
    for name, b in bound.scope.bindings.items():
        if b.target.kind in {"model", "enum", "well_known"}:
            visible_types[name] = b.target
    # Local exports also counted for unaliased self-refs
    for name, sym in bound.exports.items():
        if sym.kind in {"model", "enum", "well_known"} and name not in visible_types:
            visible_types[name] = sym

    # Check if current module imports well-known provider to allow fallback normalization
    has_well_known_import = any(
        getattr(imp, "module", None) == "@/well-known" for imp in unit.ast.imports
    )

    def _resolve_tref(t: TypeRef) -> TypeRef:
        if t.kind == "unresolved":
            name = t.name
            if name in {"int", "string", "bool", "float"}:
                return TypeRef(
                    name=name, kind="builtin", optional=getattr(t, "optional", False)
                )
            sym = visible_types.get(name)
            if sym is None:
                # Fallback: if module imports well-known provider and the name matches
                # a well-known type, resolve it as well_known even if not explicitly bound
                if has_well_known_import and name in WELL_KNOWN_TYPES:
                    return TypeRef(
                        name=name,
                        kind="well_known",
                        namespace=WELL_KNOWN_NAMESPACE,
                        absolute_id=f"{WELL_KNOWN_NAMESPACE}:{name}",
                        optional=getattr(t, "optional", False),
                    )
                return TypeRef(name=name, kind="unresolved")
            if sym.kind == "well_known":
                # Treat well-known types as models in user specs, but mark kind as well_known for codegen
                return TypeRef(
                    name=name,
                    kind="well_known",
                    namespace=sym.namespace,
                    absolute_id=sym.absolute_id,
                    optional=getattr(t, "optional", False),
                )
            if sym.kind == "model":
                return TypeRef(
                    name=name,
                    kind="model",
                    namespace=sym.namespace,
                    absolute_id=sym.absolute_id,
                    is_domain=sym.is_domain,
                    optional=getattr(t, "optional", False),
                )
            if sym.kind == "enum":
                return TypeRef(
                    name=name,
                    kind="enum",
                    namespace=sym.namespace,
                    absolute_id=sym.absolute_id,
                    is_domain=sym.is_domain,
                    optional=getattr(t, "optional", False),
                )
            return TypeRef(name=name, kind="unresolved")
        if t.kind == "container" and t.name == "list":
            # Recursively resolve inner generic argument(s)
            inner_args = []
            for arg in t.args or []:
                inner_args.append(_resolve_tref(arg))
            return TypeRef(
                name=t.name,
                kind=t.kind,
                args=inner_args,
                optional=getattr(t, "optional", False),
            )
        return t

    def _resolve_inline_struct(ret: InlineStruct) -> None:
        for rf in ret.fields:
            if isinstance(rf.type, TypeRef):
                rf.type = _resolve_tref(rf.type)

    def _walk_namespace(ns: Namespace) -> list[object]:
        out: list[object] = []
        for it in getattr(ns, "items", []) or []:
            if isinstance(it, (Rpc, Event)):
                out.append(it)
            elif isinstance(it, Namespace):
                out.extend(_walk_namespace(it))
        return out

    for d in unit.ast.decls:
        if isinstance(d, Model):
            for f in d.fields:
                if isinstance(f.type, TypeRef):
                    f.type = _resolve_tref(f.type)
        if isinstance(d, ErrorDecl):
            for p in d.params:
                if isinstance(p.type, TypeRef):
                    p.type = _resolve_tref(p.type)
        if isinstance(d, Service):
            all_items: list[object] = []
            # Include top-level RPCs and Events (emits/listens)
            all_items.extend(d.rpcs)
            all_items.extend(getattr(d, "emits", []) or [])
            all_items.extend(getattr(d, "listens", []) or [])
            for ns in getattr(d, "namespaces", []) or []:
                all_items.extend(_walk_namespace(ns))
            for it in all_items:
                if isinstance(it, Rpc):
                    for p in it.params:
                        if isinstance(p.type, TypeRef):
                            p.type = _resolve_tref(p.type)
                    if isinstance(it.returns, InlineStruct):
                        _resolve_inline_struct(it.returns)
                    elif isinstance(it.returns, TypeRef):
                        it.returns = _resolve_tref(it.returns)
                elif isinstance(it, Event):
                    for p in it.params:
                        if isinstance(p.type, TypeRef):
                            p.type = _resolve_tref(p.type)

    # Validate no unresolved types remain
    def _fail_unresolved(name: str) -> None:
        raise AmiCompileError(
            f"Unknown type '{name}'",
            file=unit.path,
            line=loc_type_usage_line(unit.path, name),
            column=None,
            stage="resolve",
            hint="Import this type or define it in the current module",
        )

    for d in unit.ast.decls:
        if isinstance(d, Model):
            for f in d.fields:
                if isinstance(f.type, TypeRef) and f.type.kind == "unresolved":
                    _fail_unresolved(f.type.name)
        if isinstance(d, ErrorDecl):
            for p in d.params:
                if isinstance(p.type, TypeRef) and p.type.kind == "unresolved":
                    _fail_unresolved(p.type.name)
        if isinstance(d, Service):
            all_items: list[object] = []
            all_items.extend(d.rpcs)
            for ns in getattr(d, "namespaces", []) or []:
                all_items.extend(_walk_namespace(ns))
            for it in all_items:
                if isinstance(it, Rpc):
                    for p in it.params:
                        if isinstance(p.type, TypeRef) and p.type.kind == "unresolved":
                            _fail_unresolved(p.type.name)
                    if isinstance(it.returns, InlineStruct):
                        for rf in it.returns.fields:
                            if (
                                isinstance(rf.type, TypeRef)
                                and rf.type.kind == "unresolved"
                            ):
                                _fail_unresolved(rf.type.name)
                    elif (
                        isinstance(it.returns, TypeRef)
                        and it.returns.kind == "unresolved"
                    ):
                        _fail_unresolved(it.returns.name)
                elif isinstance(it, Event):
                    for p in it.params:
                        if isinstance(p.type, TypeRef) and p.type.kind == "unresolved":
                            _fail_unresolved(p.type.name)

from pathlib import Path

from amic.ast.model import (
    EnumDecl,
    ErrorDecl,
    Event,
    ImportStmt,
    Infrastructure,
    InfrastructureFile,
    InlineStruct,
    Model,
    Rpc,
    Service,
    Spec,
    Subject,
    TypeRef,
)
from amic.ast.model import (
    ServiceLink as _ServiceLink,
)
from amic.binder import make_project_binder
from amic.compilation.compiled import (
    WELL_KNOWN_NAMESPACE,
    CompiledProject,
    CompiledService,
)
from amic.decorators import apply_decorators_parsed
from amic.errors import AmiToolCompileError as AmiCompileError
from amic.locate import (
    loc_error_line,
    loc_model_line,
    loc_service_line,
    loc_type_usage_line,
)
from amic.parsing.parser import parse_file as parse_one
from amic.resolver import collect_module, ns_for_file, resolve_types_in_module
from amic.semantics import run_semantics_checks


def _is_scalar_like(type_ref) -> bool:
    if not isinstance(type_ref, TypeRef):
        return False
    if type_ref.kind in {"builtin", "well_known", "enum"}:
        return True
    if type_ref.kind == "container" and type_ref.name == "list" and type_ref.args:
        return _is_scalar_like(type_ref.args[0])
    return False


def _collect_non_scalar_types(names: set, type_ref) -> None:
    """Recursively collect non-scalar TypeRefs used in signatures.

    - Builtins, well-knowns and enums are ignored
    - For containers like list[T] we collect inner type T (recursively)
    - For models/errors (non-scalar) we add the TypeRef itself
    """
    if not isinstance(type_ref, TypeRef):
        return
    if type_ref.kind in {"builtin", "well_known", "enum"}:
        return
    if type_ref.kind == "container" and type_ref.name == "list" and type_ref.args:
        _collect_non_scalar_types(names, type_ref.args[0])
        return
    names.add(type_ref)


def _gather_model_typerefs(type_ref, acc: set[TypeRef]) -> None:
    """Collect model TypeRefs referenced by a TypeRef (recursively for containers)."""
    if not isinstance(type_ref, TypeRef):
        return
    if type_ref.kind == "model":
        acc.add(type_ref)
        return
    if (
        type_ref.kind == "container"
        and getattr(type_ref, "name", None) == "list"
        and getattr(type_ref, "args", None)
    ):
        _gather_model_typerefs(type_ref.args[0], acc)


def parse_root(
    root_path: Path,
) -> tuple[Infrastructure, list[object], list[ImportStmt], Path]:
    top = parse_one(root_path)
    apply_decorators_parsed(top, file=root_path)
    if isinstance(top, InfrastructureFile):
        infra = top.infrastructure
        adj_decls = top.decls
        root_imports: list[ImportStmt] = getattr(top, "imports", [])
    elif isinstance(top, Infrastructure):
        infra = top
        adj_decls = []
        root_imports = []
    else:
        raise AmiCompileError(
            "Root file must contain infrastructure <Name> {...}",
            file=root_path,
            stage="compilation",
            hint="Add an 'infrastructure' block to the root .asl",
        )
    root_dir = root_path.parent.resolve()
    return infra, adj_decls, root_imports, root_dir


def collect_imports(root_imports: list[ImportStmt]) -> dict[str, tuple[str, str]]:
    imported_services_map: dict[str, tuple[str, str]] = {}
    for imp in root_imports:
        for item in imp.items:
            if item.kind == "service":
                ref_name = item.alias or item.name
                imported_services_map[ref_name] = (imp.module, item.name)
    return imported_services_map


def collect_services(
    infra: Infrastructure, imported_services_map: dict[str, tuple[str, str]]
) -> list[_ServiceLink]:
    links = list(infra.services)
    for ref_name in getattr(infra, "refs", []) or []:
        if ref_name in imported_services_map:
            mod_path, actual_name = imported_services_map[ref_name]
            links.append(_ServiceLink(name=actual_name, module=mod_path))
    return links


def index_decls(
    adj_decls: list[object],
) -> tuple[
    list[Model],
    list[ErrorDecl],
    list[EnumDecl],
    dict[str, Model],
    dict[str, ErrorDecl],
    dict[str, EnumDecl],
    dict[str, Model],
    dict[str, ErrorDecl],
    dict[str, EnumDecl],
]:
    global_models: list[Model] = [d for d in adj_decls if isinstance(d, Model)]
    global_errors: list[ErrorDecl] = [d for d in adj_decls if isinstance(d, ErrorDecl)]
    global_enums: list[EnumDecl] = [d for d in adj_decls if isinstance(d, EnumDecl)]
    domain_models_all: dict[str, Model] = {
        m.name: m for m in global_models if getattr(m, "domain", False)
    }
    domain_errors_all: dict[str, ErrorDecl] = {
        e.name: e for e in global_errors if getattr(e, "domain", False)
    }
    domain_enums_all: dict[str, EnumDecl] = {
        e.name: e for e in global_enums if getattr(e, "domain", False)
    }
    declared_models_index: dict[str, Model] = {m.name: m for m in global_models}
    declared_errors_index: dict[str, ErrorDecl] = {e.name: e for e in global_errors}
    declared_enums_index: dict[str, EnumDecl] = {e.name: e for e in global_enums}
    return (
        global_models,
        global_errors,
        global_enums,
        domain_models_all,
        domain_errors_all,
        domain_enums_all,
        declared_models_index,
        declared_errors_index,
        declared_enums_index,
    )


def _iter_ns_paths(ns) -> list[tuple[list[str], object]]:
    out: list[tuple[list[str], object]] = []

    def _walk(prefix: list[str], node: object) -> None:
        for it in getattr(node, "items", []) or []:
            if isinstance(it, (Rpc, Event)):
                out.append((prefix, it))
            else:
                _walk(prefix + [it.name.lower()], it)

    _walk([ns.name.lower()], ns)
    return out


def iter_rpcs(service: Service):
    for r in service.rpcs:
        yield [], r
    for ns in getattr(service, "namespaces", []) or []:
        for path, item in _iter_ns_paths(ns):
            if isinstance(item, Rpc):
                yield path, item


def iter_events(service: Service):
    for ev in getattr(service, "emits", []) or []:
        yield [], ev
    for ev in getattr(service, "listens", []) or []:
        yield [], ev
    for ns in getattr(service, "namespaces", []) or []:
        for path, item in _iter_ns_paths(ns):
            if isinstance(item, Event):
                yield path, item


def _collect_model_types_for_service_public(s: Service):
    names: set = set()
    for _path, r in iter_rpcs(s):
        for p in r.params:
            _collect_non_scalar_types(names, p.type)
        ret = r.returns
        if isinstance(ret, InlineStruct):
            for f in ret.fields:
                _collect_non_scalar_types(names, f.type)
        else:
            _collect_non_scalar_types(names, ret)
    for _path, ev in iter_events(s):
        for p in ev.params:
            _collect_non_scalar_types(names, p.type)
    return names


def _process_imported_service_link(
    *,
    root_path: Path,
    root_dir: Path,
    link: _ServiceLink,
    processed_files: set[Path],
    declared_models_index: dict[str, Model],
    declared_errors_index: dict[str, ErrorDecl],
    domain_models_all: dict[str, Model],
    domain_errors_all: dict[str, ErrorDecl],
    domain_enums_all: dict[str, EnumDecl],
    include_all_models: bool = False,
) -> CompiledService:
    unit = collect_module(root_dir, root_path, link.module)
    processed_files.add(unit.path)
    if not unit.ast.module:
        raise AmiCompileError(
            "Module declaration is required",
            file=unit.path,
            stage="compilation",
            hint="Add 'module \"<namespace>\";' at the top of the file",
        )
    service_ns = unit.ast.module or ns_for_file(root_dir, unit.path)
    for d in unit.ast.decls:
        if isinstance(d, Model) and getattr(d, "domain", False):
            domain_models_all.setdefault(d.name, d)
        if isinstance(d, ErrorDecl) and getattr(d, "domain", False):
            domain_errors_all.setdefault(d.name, d)
        if isinstance(d, EnumDecl) and getattr(d, "domain", False):
            domain_enums_all.setdefault(d.name, d)
        # enums are scalar-like; no boundary check here

    # Resolve types within the imported module context using Binder
    binder = make_project_binder()
    resolve_types_in_module(unit, binder=binder, root_dir=root_dir)

    svc_decls = [
        d for d in unit.ast.decls if isinstance(d, Service) and d.name == link.name
    ]
    if not svc_decls:
        raise AmiCompileError(
            f"Service {link.name} not found in the module",
            file=unit.path,
            stage="compilation",
            hint="Ensure the file contains 'service <Name> { ... }'",
        )
    svc = svc_decls[0]

    local_models = [d for d in unit.ast.decls if isinstance(d, Model)]
    local_errors = [d for d in unit.ast.decls if isinstance(d, ErrorDecl)]
    local_enums = [
        d
        for d in unit.ast.decls
        if isinstance(d, EnumDecl) and not getattr(d, "domain", False)
    ]

    # Track module namespace for every model we encounter (local or from imports)
    model_ns_index: dict[str, str] = {m.name: service_ns for m in local_models}

    imported_error_index: dict[str, tuple[str, ErrorDecl]] = {}
    imported_model_index: dict[str, tuple[str, Model]] = {}
    for imp in unit.ast.imports:
        sub_unit = collect_module(root_dir, unit.path, imp.module)
        processed_files.add(sub_unit.path)
        if not sub_unit.ast.module:
            raise AmiCompileError(
                "Module declaration is required",
                file=sub_unit.path,
                stage="compilation",
                hint="Add 'module \"<namespace>\";' at the top of the file",
            )
        # Aggregate domain models/errors/enums from imported submodules into the project-wide registry
        # so that root-level generation (models.py/errors.py) sees them.
        for d in sub_unit.ast.decls:
            if isinstance(d, Model) and getattr(d, "domain", False):
                domain_models_all.setdefault(d.name, d)
            if isinstance(d, ErrorDecl) and getattr(d, "domain", False):
                domain_errors_all.setdefault(d.name, d)
            if isinstance(d, EnumDecl) and getattr(d, "domain", False):
                domain_enums_all.setdefault(d.name, d)
            # non-domain enums from same service namespace should be generated locally for service
            if isinstance(d, EnumDecl) and not getattr(d, "domain", False):
                same_scope = bool(
                    sub_unit.ns
                    and (
                        sub_unit.ns == service_ns
                        or sub_unit.ns.startswith(service_ns + ".")
                    )
                )
                if same_scope and all(e.name != d.name for e in local_enums):
                    local_enums.append(d)
            if isinstance(d, Model):
                model_ns_index.setdefault(d.name, sub_unit.ns)
        # Ensure imported module types are resolved for visibility
        resolve_types_in_module(sub_unit, binder=binder, root_dir=root_dir)
        for item in imp.items:
            if item.kind == "error":
                matches = [
                    d
                    for d in sub_unit.ast.decls
                    if isinstance(d, ErrorDecl) and d.name == item.name
                ]
                if matches:
                    imported_error_index[item.name] = (sub_unit.ns, matches[0])
            elif item.kind == "model":
                matches_m = [
                    d
                    for d in sub_unit.ast.decls
                    if isinstance(d, Model) and d.name == item.name
                ]
                if matches_m:
                    imported_model_index[item.name] = (sub_unit.ns, matches_m[0])
        for d in sub_unit.ast.decls:
            if isinstance(d, Model) and d.name not in declared_models_index:
                declared_models_index[d.name] = d
            if isinstance(d, ErrorDecl) and d.name not in declared_errors_index:
                declared_errors_index[d.name] = d
            # Track imported enums locally for the service; declared_enums_index is in outer scope

    rpc_error_modules: dict[str, list[str]] = {}
    dep_error_modules: dict[str, list[ErrorDecl]] = {}
    local_error_names = {e.name for e in local_errors}
    for _path, rpc in iter_rpcs(svc):
        mods: list[str] = []
        for a in rpc.attrs:
            if a.name == "throws":
                for arg in a.args:
                    err_name = str(arg)
                    if err_name in local_error_names:
                        continue
                    if err_name in imported_error_index:
                        mod_ns, err_decl = imported_error_index[err_name]
                        # Skip domain errors: their classes and registry are generated at the root level
                        if getattr(err_decl, "domain", False):
                            continue
                        if mod_ns not in mods:
                            mods.append(mod_ns)
                        dep_error_modules.setdefault(mod_ns, [])
                        if all(
                            e.name != err_decl.name for e in dep_error_modules[mod_ns]
                        ):
                            dep_error_modules[mod_ns].append(err_decl)
                    else:
                        raise AmiCompileError(
                            f"RPC {svc.name}.{rpc.name} references unknown error {err_name}",
                            file=unit.path,
                            stage="compilation",
                            hint="Import the error or define it locally in this module",
                        )
        rpc_error_modules[rpc.name] = mods

    # Additionally, include all imported errors from modules within the same service namespace
    # into dep_error_modules so that generator can produce classes even if not referenced in @throws.
    for imp in unit.ast.imports:
        sub_unit = collect_module(root_dir, unit.path, imp.module)
        # Only consider modules within the same service namespace
        same_scope = bool(
            sub_unit.ns
            and (sub_unit.ns == service_ns or sub_unit.ns.startswith(service_ns + "."))
        )
        if not same_scope:
            continue
        for item in imp.items:
            if item.kind == "error":
                matches = [
                    d
                    for d in sub_unit.ast.decls
                    if isinstance(d, ErrorDecl) and d.name == item.name
                ]
                if not matches:
                    continue
                # Skip domain errors; they belong to the root registry
                if getattr(matches[0], "domain", False):
                    continue
                dep_error_modules.setdefault(sub_unit.ns, [])
                if all(
                    e.name != matches[0].name for e in dep_error_modules[sub_unit.ns]
                ):
                    dep_error_modules[sub_unit.ns].append(matches[0])

    used_types = _collect_model_types_for_service_public(svc)
    # Expand used_types with transitive model dependencies from local model declarations.
    # This ensures helper models referenced by fields (e.g., MessageEntity, TelegramMedia)
    # are also considered for inclusion without relying on ad-hoc post-processing.
    if used_types:
        local_model_by_name: dict[str, Model] = {m.name: m for m in local_models}
        visited: set[str] = set()
        queue: list[str] = [
            t.name
            for t in used_types
            if t.kind == "model" and t.name in local_model_by_name
        ]
        visited.update(queue)
        while queue:
            current_name = queue.pop()
            decl = local_model_by_name.get(current_name)
            if not decl:
                continue
            for f in decl.fields:
                deps: set[TypeRef] = set()
                _gather_model_typerefs(f.type, deps)
                for tref in deps:
                    used_types.add(tref)
                    nm = tref.name
                    if nm in local_model_by_name and nm not in visited:
                        visited.add(nm)
                        queue.append(nm)
    domain_models = [m for m in local_models if getattr(m, "domain", False)]
    non_domain_models = [m for m in local_models if not getattr(m, "domain", False)]
    domain_errors = [e for e in local_errors if getattr(e, "domain", False)]
    non_domain_errors = [e for e in local_errors if not getattr(e, "domain", False)]
    local_model_names = {m.name for m in non_domain_models}
    imported_model_modules: dict[str, str] = {}
    for t in list(used_types):
        if t.kind in {"builtin", "well_known"}:
            continue
        tname = t.name
        if tname in local_model_names:
            continue
        if tname in imported_model_index:
            mod_ns, model_decl = imported_model_index[tname]
            same_scope = bool(
                mod_ns and (mod_ns == service_ns or mod_ns.startswith(service_ns + "."))
            )
            if mod_ns == WELL_KNOWN_NAMESPACE:
                imported_model_modules[tname] = WELL_KNOWN_NAMESPACE
                continue
            if not getattr(model_decl, "domain", False):
                if not same_scope:
                    raise AmiCompileError(
                        f"Service {svc.name} references a non-domain model {tname} from external module {mod_ns}",
                        file=unit.path,
                        stage="compilation",
                        hint="Mark the model as 'domain' or duplicate it within the service scope",
                    )
                if all(m.name != model_decl.name for m in non_domain_models):
                    non_domain_models.append(model_decl)
                    local_model_names.add(model_decl.name)
            else:
                imported_model_modules[tname] = "__DOMAIN__"
        else:
            raise AmiCompileError(
                f"Service {svc.name} references model {tname} which is not imported",
                file=unit.path,
                line=loc_type_usage_line(unit.path, tname)
                or loc_service_line(unit.path, svc.name),
                column=None,
                stage="compilation",
                hint="Add the appropriate import in the service module",
            )

    # Perform transitive closure of model dependencies for included models (local or imported within same scope)
    if non_domain_models:
        included_names: set[str] = set(local_model_names)
        # Build name->decl for quick lookup from local and declared indices
        local_decl_by_name: dict[str, Model] = {m.name: m for m in local_models}
        queue: list[str] = list(included_names)
        while queue:
            current_name = queue.pop()
            # Retrieve model decl from local or declared indices
            decl = local_decl_by_name.get(current_name) or declared_models_index.get(
                current_name
            )
            if not decl:
                continue
            # Iterate field model type dependencies
            for f in decl.fields:
                deps: set[TypeRef] = set()
                _gather_model_typerefs(f.type, deps)
                for tref in deps:
                    dep_name = tref.name
                    if dep_name in included_names:
                        continue
                    # Resolve decl and namespace for dependency
                    dep_decl = local_decl_by_name.get(
                        dep_name
                    ) or declared_models_index.get(dep_name)
                    dep_ns = model_ns_index.get(dep_name)
                    if dep_decl is None or not dep_ns:
                        # Not visible; require explicit import
                        raise AmiCompileError(
                            f"Service {svc.name} references model {dep_name} via field dependency but it is not imported",
                            file=unit.path,
                            stage="compilation",
                            hint="Import the model in the service module to make it available",
                        )
                    # Allow domain models but do not include them locally
                    if getattr(dep_decl, "domain", False):
                        imported_model_modules[dep_name] = "__DOMAIN__"
                        continue
                    same_scope = bool(
                        dep_ns
                        and (
                            dep_ns == service_ns or dep_ns.startswith(service_ns + ".")
                        )
                    )
                    if not same_scope:
                        raise AmiCompileError(
                            f"Service {svc.name} references a non-domain model {dep_name} from external module {dep_ns} via field dependency",
                            file=unit.path,
                            stage="compilation",
                            hint="Mark the model as 'domain' or duplicate it within the service scope",
                        )
                    # Include dependency
                    non_domain_models.append(dep_decl)
                    imported_model_modules.setdefault(dep_name, dep_ns)
                    included_names.add(dep_name)
                    queue.append(dep_name)

    # If requested, include all reachable non-domain models imported from the same service namespace,
    # even if they are not referenced in RPCs/events directly.
    if include_all_models:
        for name, (mod_ns, model_decl) in imported_model_index.items():
            if getattr(model_decl, "domain", False):
                # Domain models are provided via root models and should not be duplicated locally
                continue
            same_scope = bool(
                mod_ns and (mod_ns == service_ns or mod_ns.startswith(service_ns + "."))
            )
            if not same_scope:
                # Keep the existing rule: external non-domain models are not allowed
                continue
            if all(m.name != model_decl.name for m in non_domain_models):
                non_domain_models.append(model_decl)
                local_model_names.add(model_decl.name)

    non_domain_names_all = {m.name for m in non_domain_models}
    for m in domain_models:
        for f in m.fields:
            tname = f.type.name
            if tname in non_domain_names_all:
                raise AmiCompileError(
                    f"Domain model {m.name} references non-domain {tname} in service {svc.name}",
                    file=unit.path,
                    line=loc_model_line(unit.path, m.name)
                    or loc_type_usage_line(unit.path, tname)
                    or loc_service_line(unit.path, svc.name),
                    column=None,
                    stage="compilation",
                    hint="Change field dependencies or make the target model domain",
                )
    for e in domain_errors:
        for p in e.params:
            if p.type.name in non_domain_names_all:
                raise AmiCompileError(
                    f"Domain error {e.name} uses non-domain model {p.type.name} in service {svc.name}",
                    file=unit.path,
                    line=loc_error_line(unit.path, e.name)
                    or loc_type_usage_line(unit.path, p.type.name)
                    or loc_service_line(unit.path, svc.name),
                    column=None,
                    stage="compilation",
                    hint="Use a domain model in the error parameters",
                )

    return CompiledService(
        name=link.name,
        module=service_ns,
        service=svc,
        local_models=local_models,
        local_errors=local_errors,
        dep_error_modules=dep_error_modules,
        rpc_error_modules=rpc_error_modules,
        imported_model_modules=imported_model_modules,
        domain_models=domain_models,
        domain_errors=domain_errors,
        non_domain_models=non_domain_models,
        non_domain_errors=non_domain_errors,
        local_enums=local_enums,
    )


def _process_local_service_decl(
    *,
    root_path: Path,
    infra_service: Service,
    global_models: list[Model],
    global_errors: list[ErrorDecl],
) -> CompiledService:
    service_ns = infra_service.name.lower()
    local_models: list[Model] = list(global_models)
    local_errors: list[ErrorDecl] = list(global_errors)
    dep_error_modules: dict[str, list[ErrorDecl]] = {}
    rpc_error_modules: dict[str, list[str]] = {}
    local_error_names = {e.name for e in local_errors}

    def _iter_rpcs_local(s: Service):
        for r in s.rpcs:
            yield [], r
        for ns in getattr(s, "namespaces", []) or []:
            for path, item in _iter_ns_paths(ns):
                if isinstance(item, Rpc):
                    yield path, item

    for _path, rpc in _iter_rpcs_local(infra_service):
        mods: list[str] = []
        for a in rpc.attrs:
            if a.name == "throws":
                for arg in a.args:
                    err_name = str(arg)
                    if err_name in local_error_names:
                        continue
                    else:
                        raise AmiCompileError(
                            f"RPC {infra_service.name}.{rpc.name} references unknown error {err_name}",
                            file=root_path,
                            stage="compilation",
                            hint="Define the error in the root file next to 'infrastructure'",
                        )
        rpc_error_modules[rpc.name] = mods

    used_types = set()
    for _path, r in _iter_rpcs_local(infra_service):
        for p in r.params:
            if not _is_scalar_like(p.type):
                used_types.add(p.type)
        ret = r.returns
        if isinstance(ret, InlineStruct):
            for f in ret.fields:
                if not _is_scalar_like(f.type):
                    used_types.add(f.type)
        else:
            if not _is_scalar_like(ret):
                used_types.add(ret)
    have_local = {m.name for m in local_models}
    missing = [t.name for t in used_types if t.name not in have_local]
    if missing:
        raise AmiCompileError(
            f"Service {infra_service.name} references missing models: {', '.join(missing)}",
            file=root_path,
            stage="compilation",
            hint="Add these models to the root file next to 'infrastructure'",
        )

    return CompiledService(
        name=infra_service.name,
        module=service_ns,
        service=infra_service,
        local_models=local_models,
        local_errors=local_errors,
        dep_error_modules=dep_error_modules,
        rpc_error_modules=rpc_error_modules,
        imported_model_modules={},
    )


def build_compiled_services(
    *,
    root_path: Path,
    root_dir: Path,
    infra: Infrastructure,
    imported_services_map: dict[str, tuple[str, str]],
    declared_models_index: dict[str, Model],
    declared_errors_index: dict[str, ErrorDecl],
    domain_models_all: dict[str, Model],
    domain_errors_all: dict[str, ErrorDecl],
    domain_enums_all: dict[str, EnumDecl],
    adj_decls: list[object],
    include_all_models: bool = False,
) -> tuple[list[CompiledService], set[Path], dict[str, Model], dict[str, ErrorDecl]]:
    compiled_services: list[CompiledService] = []
    processed_files: set[Path] = {root_path}
    used_service_modules: dict[str, str] = {}
    links_to_process = collect_services(infra, imported_services_map)

    for link in links_to_process:
        # prevent duplicate module namespace reuse for different services
        unit = collect_module(root_dir, root_path, link.module)
        processed_files.add(unit.path)
        if not unit.ast.module:
            raise AmiCompileError(
                "Module declaration is required",
                file=unit.path,
                stage="compilation",
                hint="Add 'module \"<namespace>\";' at the top of the file",
            )
        service_ns = unit.ast.module or ns_for_file(root_dir, unit.path)
        if (
            service_ns in used_service_modules
            and used_service_modules[service_ns] != link.name
        ):
            raise AmiCompileError(
                f"Duplicate module '{service_ns}' used for different services",
                file=unit.path,
                stage="compilation",
                hint=f"This module is already used for service '{used_service_modules[service_ns]}'. Change the namespace in 'module ...'",
            )
        used_service_modules[service_ns] = link.name

        compiled_services.append(
            _process_imported_service_link(
                root_path=root_path,
                root_dir=root_dir,
                link=link,
                processed_files=processed_files,
                declared_models_index=declared_models_index,
                declared_errors_index=declared_errors_index,
                domain_models_all=domain_models_all,
                domain_errors_all=domain_errors_all,
                domain_enums_all=domain_enums_all,
                include_all_models=include_all_models,
            )
        )

    name_to_local: dict[str, Service] = {
        s.name: s for s in [d for d in adj_decls if isinstance(d, Service)]
    }
    for ref_name in getattr(infra, "refs", []) or []:
        if ref_name in imported_services_map:
            continue
        if ref_name not in name_to_local:
            raise AmiCompileError(
                f"Service '{ref_name}' not found locally or in imports",
                file=root_path,
                stage="compilation",
                hint="Either declare the service next to 'infrastructure' or import it in the file header",
            )
    for svc in name_to_local.values():
        compiled_services.append(
            _process_local_service_decl(
                root_path=root_path,
                infra_service=svc,
                global_models=[d for d in adj_decls if isinstance(d, Model)],
                global_errors=[d for d in adj_decls if isinstance(d, ErrorDecl)],
            )
        )

    return compiled_services, processed_files, domain_models_all, domain_errors_all


def assemble_compiled_project(
    *,
    infra: Infrastructure,
    compiled_services: list[CompiledService],
    domain_models_all: dict[str, Model],
    domain_errors_all: dict[str, ErrorDecl],
    domain_enums_all: dict[str, EnumDecl],
) -> CompiledProject:
    subject_name = _determine_subject_name(infra)
    subject = Subject(name=subject_name)
    decls: list[object] = []
    decls.extend([cs.service for cs in compiled_services])
    spec = Spec(subject=subject, decls=decls, errors=list(domain_errors_all.values()))
    return CompiledProject(
        spec=spec,
        subject_prefix=subject_name,
        services=compiled_services,
        domain_models=list(domain_models_all.values()),
        domain_errors=list(domain_errors_all.values()),
        domain_enums=list(domain_enums_all.values()),
        acl=getattr(infra, "acl", None),
    )


def _determine_subject_name(infra: Infrastructure) -> str:
    def _snake(name: str) -> str:
        out = []
        for i, ch in enumerate(name):
            if ch.isupper() and i > 0 and (not name[i - 1].isupper()):
                out.append("_")
            out.append(ch.lower())
        return "".join(out)

    subject_name = _snake(infra.name)
    for a in infra.attrs or []:
        if a.name == "subject":
            if a.args:
                subject_name = str(a.args[0])
            elif a.kwargs.get("value"):
                subject_name = str(a.kwargs["value"])
    return subject_name


def compile_infrastructure(
    root_path: Path, *, include_all_models: bool = False
) -> CompiledProject:
    infra, adj_decls, root_imports, root_dir = parse_root(root_path)

    (
        global_models,
        global_errors,
        global_enums,
        domain_models_all,
        domain_errors_all,
        domain_enums_all,
        declared_models_index,
        declared_errors_index,
        declared_enums_index,
    ) = index_decls(adj_decls)

    imported_services_map = collect_imports(root_imports)

    compiled_services, processed_files, domain_models_all, domain_errors_all = (
        build_compiled_services(
            root_path=root_path,
            root_dir=root_dir,
            infra=infra,
            imported_services_map=imported_services_map,
            declared_models_index=declared_models_index,
            declared_errors_index=declared_errors_index,
            domain_models_all=domain_models_all,
            domain_errors_all=domain_errors_all,
            domain_enums_all=domain_enums_all,
            adj_decls=adj_decls,
            include_all_models=include_all_models,
        )
    )

    run_semantics_checks(
        root_path=root_path,
        domain_models_all=domain_models_all,
        declared_models_index=declared_models_index,
        processed_files=processed_files,
        compiled_services=compiled_services,
        acl=getattr(infra, "acl", None),
    )

    return assemble_compiled_project(
        infra=infra,
        compiled_services=compiled_services,
        domain_models_all=domain_models_all,
        domain_errors_all=domain_errors_all,
        domain_enums_all=domain_enums_all,
    )

from pathlib import Path

from amic.ast.model import (
    AclRule,
    Event,
    Model,
    Namespace,
    Rpc,
    Service,
    TypeRef,
)
from amic.compilation.compiled import CompiledService
from amic.errors import AmiToolCompileError as AmiCompileError
from amic.locate import (
    loc_model_line,
    loc_type_usage_line,
)


def run_semantics_checks(
    *,
    root_path: Path,
    domain_models_all: dict[str, Model],
    declared_models_index: dict[str, Model],
    processed_files: set[Path],
    compiled_services: list[CompiledService] | None = None,
    acl: list[AclRule] | None = None,
) -> None:
    _validate_domain_boundary(
        root_path=root_path,
        domain_models_all=domain_models_all,
        declared_models_index=declared_models_index,
        processed_files=processed_files,
    )
    _validate_acl(
        root_path=root_path,
        compiled_services=compiled_services or [],
        acl=acl or [],
    )


def _is_scalar_like(type_ref: object) -> bool:
    if not isinstance(type_ref, TypeRef):
        return False
    if type_ref.kind in {"builtin", "well_known", "enum"}:
        return True
    if (
        type_ref.kind == "container"
        and getattr(type_ref, "name", None) == "list"
        and getattr(type_ref, "args", None)
    ):
        inner = type_ref.args[0]
        return _is_scalar_like(inner)
    return False


def _validate_domain_boundary(
    *,
    root_path: Path,
    domain_models_all: dict[str, Model],
    declared_models_index: dict[str, Model],
    processed_files: set[Path],
) -> None:
    for dm_name, dm in domain_models_all.items():
        for f in getattr(dm, "fields", []) or []:
            t = f.type
            if _is_scalar_like(t):
                continue
            ref_decl = declared_models_index.get(getattr(t, "name", None))
            if ref_decl is not None and not getattr(ref_decl, "domain", False):
                report_file: Path = root_path
                report_line: int | None = None
                for pth in processed_files:
                    ln = loc_model_line(pth, dm_name)
                    if ln:
                        report_file = pth
                        use_ln = loc_type_usage_line(pth, getattr(t, "name", ""))
                        report_line = use_ln or ln
                        break
                raise AmiCompileError(
                    f"Domain model {dm_name} must not reference non-domain model {getattr(t, 'name', t)}",
                    file=report_file,
                    line=report_line,
                    column=None,
                    stage="semantics",
                    hint="Use a domain model for this field or refactor the domain boundary",
                )


def _walk_namespace(ns: Namespace, prefix: list[str]) -> list[tuple[list[str], object]]:
    out: list[tuple[list[str], object]] = []
    current = prefix + [ns.name.lower()]
    for it in getattr(ns, "items", []) or []:
        if isinstance(it, (Rpc, Event)):
            out.append((current, it))
        elif isinstance(it, Namespace):
            out.extend(_walk_namespace(it, current))
    return out


def _iter_rpcs(service: Service) -> list[tuple[list[str], Rpc]]:
    out: list[tuple[list[str], Rpc]] = []
    for r in service.rpcs:
        out.append(([], r))
    for ns in getattr(service, "namespaces", []) or []:
        for path, item in _walk_namespace(ns, []):
            if isinstance(item, Rpc):
                out.append((path, item))
    return out


def _iter_events(service: Service) -> list[tuple[list[str], Event]]:
    out: list[tuple[list[str], Event]] = []
    for e in getattr(service, "emits", []) or []:
        out.append(([], e))
    for e in getattr(service, "listens", []) or []:
        out.append(([], e))
    for ns in getattr(service, "namespaces", []) or []:
        for path, item in _walk_namespace(ns, []):
            if isinstance(item, Event):
                out.append((path, item))
    return out


def _validate_acl(
    *,
    root_path: Path,
    compiled_services: list[CompiledService],
    acl: list[AclRule],
) -> None:
    if not acl:
        return
    name_to_service: dict[str, Service] = {
        cs.name: cs.service for cs in compiled_services
    }

    def _find_rpc(svc: Service, path: list[str]) -> bool:
        for p, r in _iter_rpcs(svc):
            full = p + [r.name.lower()]
            if full == [seg.lower() for seg in path]:
                return True
        return False

    def _find_event(svc: Service, path: list[str]) -> bool:
        for p, e in _iter_events(svc):
            full = p + [e.name.lower()]
            if full == [seg.lower() for seg in path]:
                return True
        return False

    for rule in acl:
        subj = rule.subject
        if subj not in name_to_service:
            raise AmiCompileError(
                f"ACL rule subject '{subj}' does not match any known service",
                file=root_path,
                stage="semantics",
                hint="Ensure the service is declared locally or imported in 'infrastructure'",
            )
        for act in rule.actions or []:
            # Expected target format: Service[.namespace_path].(rpc|emit)
            target = act.target
            if not target or "." not in target:
                raise AmiCompileError(
                    f"ACL target '{target}' must be qualified as Service.path",
                    file=root_path,
                    stage="semantics",
                    hint="Use 'Service.rpcName' or 'Service.ns.rpcName' / 'Service.eventName'",
                )
            parts = target.split(".")
            target_service_name = parts[0]
            target_path = parts[1:]
            target_service = name_to_service.get(target_service_name)
            if target_service is None:
                raise AmiCompileError(
                    f"ACL target references unknown service '{target_service_name}'",
                    file=root_path,
                    stage="semantics",
                    hint="Ensure the target service exists and is referenced in 'infrastructure'",
                )
            if act.kind == "call":
                if not _find_rpc(target_service, target_path):
                    raise AmiCompileError(
                        f"ACL call target '{target}' does not match any RPC",
                        file=root_path,
                        stage="semantics",
                        hint="Check RPC name and namespaces in the target service",
                    )
            elif act.kind == "listen":
                # listen is allowed only against events that the target service EMITS
                if not _find_event(target_service, target_path):
                    raise AmiCompileError(
                        f"ACL listen target '{target}' does not match any emit-event",
                        file=root_path,
                        stage="semantics",
                        hint="Check emitted event name and namespaces in the target service",
                    )
            else:
                raise AmiCompileError(
                    f"Unknown ACL action kind '{act.kind}' for target '{target}'",
                    file=root_path,
                    stage="semantics",
                    hint="Use 'call' or 'listen'",
                )

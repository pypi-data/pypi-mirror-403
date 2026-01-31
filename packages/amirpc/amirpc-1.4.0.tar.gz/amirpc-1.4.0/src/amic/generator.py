import ast
import shutil
from pathlib import Path

from amic.ast.model import InlineStruct, Service, TypeRef
from amic.codegen.clients import render_client_module
from amic.codegen.emit import format_code
from amic.codegen.enums import render_domain_enums, render_service_enums
from amic.codegen.errors import render_domain_errors, render_service_errors
from amic.codegen.events import render_events_module
from amic.codegen.models import render_domain_models
from amic.codegen.models_service import render_service_models_module
from amic.codegen.servers import render_server_module
from amic.codegen.utils import (
    emit_well_known_imports,
    enum_names_in,
    is_builtin_or_well_known,
    iter_emits,
    iter_events,
    iter_listens,
    iter_rpcs,
    model_types_in,
    request_payload_name,
    resolve_import_module,
    response_result_name,
    snake,
    type_has_optional,
)
from amic.compilation.compiled import CompiledProject


def generate_project(project: CompiledProject, out_dir: Path) -> list[Path]:
    # clean output
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    # package init (no re-exports)
    (out_dir / "__init__.py").write_text("", encoding="utf-8")
    written.append(out_dir / "__init__.py")
    # PEP 561: mark package as typed
    (out_dir / "py.typed").write_text("", encoding="utf-8")
    written.append(out_dir / "py.typed")

    # Root models.py (domain) and errors.py (domain) + enums.py (domain)
    root_models_code = render_domain_models(project.domain_models)
    (out_dir / "models.py").write_text(root_models_code, encoding="utf-8")
    written.append(out_dir / "models.py")
    # domain enums
    enums_code = render_domain_enums(getattr(project, "domain_enums", []) or [])
    if enums_code.strip():
        (out_dir / "enums.py").write_text(enums_code + "\n", encoding="utf-8")
        written.append(out_dir / "enums.py")
    # errors
    e_code = render_domain_errors(project.domain_errors, project.domain_models)
    (out_dir / "errors.py").write_text(e_code + "\n", encoding="utf-8")
    written.append(out_dir / "errors.py")

    # Per service generation: local models, local errors, client
    for svc in project.services:
        srv_dir = out_dir / snake(svc.name)
        srv_dir.mkdir(parents=True, exist_ok=True)
        init_code = (
            f"from .client import {svc.name}Client\n"
            f"from .server import {svc.name}Server\n"
            f"from .events import {svc.name}Emitter\n"
            f"__all__ = ['{svc.name}Client', '{svc.name}Server', '{svc.name}Emitter']\n"
        )
        (srv_dir / "__init__.py").write_text(init_code, encoding="utf-8")
        written.append(srv_dir / "__init__.py")

        # local models.py: request/response/event payloads only (moved generation below)

        # local errors.py
        l_code = render_service_errors(project, svc)
        (srv_dir / "errors.py").write_text(l_code + "\n", encoding="utf-8")
        written.append(srv_dir / "errors.py")

        # local enums.py (always generate, even if empty → create empty file for stable imports)
        enums_code_local = render_service_enums(getattr(svc, "local_enums", []) or [])
        (srv_dir / "enums.py").write_text(
            (enums_code_local + "\n") if enums_code_local.strip() else "",
            encoding="utf-8",
        )
        written.append(srv_dir / "enums.py")

        # Build models.py for service (request/response + event payloads)
        models_code = render_service_models_module(project, svc)
        (srv_dir / "models.py").write_text(models_code, encoding="utf-8")
        written.append(srv_dir / "models.py")

        # client.py for service, with proper imports and per-RPC error mappings from @throws
        client_code = render_client_module(project.subject_prefix, svc.service)

        # Now inject type imports for local and external models (client-visible only: params + simple returns)
        def _collect_client_visible_types(service: Service) -> set[TypeRef]:
            names: set[TypeRef] = set()
            for _path, rpc in iter_rpcs(service):
                # Collect types from params (client method signatures use these types directly)
                for p in rpc.params:
                    if isinstance(p.type, TypeRef):
                        inner_models = model_types_in(p.type)
                        if inner_models:
                            names.update(inner_models)
                        elif not is_builtin_or_well_known(p.type):
                            names.add(p.type)
                # Collect types from returns
                if isinstance(rpc.returns, TypeRef):
                    # If return is a container (e.g., list[Model]), collect inner model types
                    inner_models = model_types_in(rpc.returns)
                    if inner_models:
                        names.update(inner_models)
                    elif not is_builtin_or_well_known(rpc.returns):
                        names.add(rpc.returns)
            return names

        needed_types = sorted(
            _collect_client_visible_types(svc.service), key=lambda t: t.name
        )
        # Import non-domain models defined within the service package (local to service)
        local_model_names = {m.name for m in (svc.non_domain_models or [])}
        local_needed = [n.name for n in needed_types if n.name in local_model_names]
        # Import external models from other modules within the same service namespace
        external_needed_by_module: dict[str, list[str]] = {}
        for t in needed_types:
            if t.name in local_model_names:
                continue
            mod = svc.imported_model_modules.get(t.name)
            if mod and mod not in ("__DOMAIN__", "__WELL_KNOWN__"):
                external_needed_by_module.setdefault(mod, []).append(t.name)

        # Prepend imports accordingly
        new_body: list[ast.stmt] = []
        # minimal header imports for client
        new_body.append(
            ast.ImportFrom(
                module="amirpc",
                names=[ast.alias(name="BaseClient"), ast.alias(name="Runtime")],
                level=0,
            )
        )
        # Drop unused typing/functools imports in minimal client module
        # Domain first: import domain models used in simple returns
        domain_names = {m.name for m in (project.domain_models or [])}
        domain_needed = [n.name for n in needed_types if n.name in domain_names]
        if domain_needed:
            new_body.append(
                ast.ImportFrom(
                    module="models",
                    names=[ast.alias(name=n) for n in sorted(set(domain_needed))],
                    level=2,
                )
            )
        # Import enums referenced anywhere in client-visible signatures (params and returns)
        enum_needed_names: set[str] = set()
        for _path, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef):
                    enum_needed_names.update(enum_names_in(p.type))
            if isinstance(rpc.returns, TypeRef):
                enum_needed_names.update(enum_names_in(rpc.returns))
        local_enum_names = {e.name for e in (getattr(svc, "local_enums", []) or [])}
        domain_enum_names = {
            e.name for e in (getattr(project, "domain_enums", []) or [])
        }
        to_import_local = sorted(enum_needed_names & local_enum_names)
        to_import_domain = sorted(
            (enum_needed_names - set(local_enum_names)) & domain_enum_names
        )
        if to_import_local:
            new_body.append(
                ast.ImportFrom(
                    module="enums",
                    names=[ast.alias(name=n) for n in to_import_local],
                    level=1,
                )
            )
        if to_import_domain:
            new_body.append(
                ast.ImportFrom(
                    module="enums",
                    names=[ast.alias(name=n) for n in to_import_domain],
                    level=2,
                )
            )
        if local_needed:
            new_body.append(
                ast.ImportFrom(
                    module="models",
                    names=[ast.alias(name=n) for n in local_needed],
                    level=1,
                )
            )
        # Import payload/result classes for client methods
        payload_result_names: list[str] = []
        for ns_path, r in iter_rpcs(svc.service):
            payload_result_names.append(
                request_payload_name(svc.service, r, ns_path)
            )  # XxxPayload for request construction
            if isinstance(r.returns, InlineStruct):
                payload_result_names.append(
                    response_result_name(svc.service, r, ns_path)
                )  # XxxResult for return type
        # Event payloads for emit/listen
        from amic.codegen.utils import emit_payload_name, listen_payload_name

        event_payload_names: list[str] = []
        for ns_path, ev in iter_events(svc.service):
            # decide by role suffix
            if getattr(ev, "role", None) == "emit":
                event_payload_names.append(emit_payload_name(svc.service, ev, ns_path))
            elif getattr(ev, "role", None) == "listen":
                event_payload_names.append(
                    listen_payload_name(svc.service, ev, ns_path)
                )
        import_names = sorted(set(payload_result_names))
        # include event payloads too
        all_import_names = sorted(set(import_names + event_payload_names))
        if all_import_names:
            new_body.append(
                ast.ImportFrom(
                    module="models",
                    names=[ast.alias(name=n) for n in all_import_names],
                    level=1,
                )
            )
        for mod_path, names in sorted(external_needed_by_module.items()):
            module_name, level = resolve_import_module(svc.module, mod_path, "models")
            new_body.append(
                ast.ImportFrom(
                    module=module_name,
                    names=[ast.alias(name=n) for n in sorted(set(names))],
                    level=level,
                )
            )

        # No fallback: enforce explicit resolution to the correct module bucket

        # import error registries (local/external) and domain registry from root with aliases
        error_registry_aliases: list[str] = []
        # domain registry
        new_body.append(
            ast.ImportFrom(
                module="errors",
                names=[ast.alias(name="ERRORS", asname="__DOMAIN_ERRORS")],
                level=2,
            )
        )
        error_registry_aliases.append("__DOMAIN_ERRORS")
        # local registry
        new_body.append(
            ast.ImportFrom(
                module="errors",
                names=[ast.alias(name="ERRORS", asname="__LOCAL_ERRORS")],
                level=1,
            )
        )
        error_registry_aliases.append("__LOCAL_ERRORS")
        # external registries (skip same-module namespace; it's already covered by __LOCAL_ERRORS)
        for mod_path in sorted(svc.dep_error_modules.keys()):
            if mod_path == svc.module:
                continue

            # Well-known errors import from amirpc.errors (not relative)
            if mod_path == "__WELL_KNOWN__":
                module_name = "amirpc.errors"
                level = 0
                alias = "__EXT_ERRORS___WELL_KNOWN__"
            else:
                module_name, level = resolve_import_module(
                    svc.module, mod_path, "errors"
                )
                alias = "__EXT_ERRORS_" + module_name.replace(".", "_")

            new_body.append(
                ast.ImportFrom(
                    module=module_name,
                    names=[ast.alias(name="ERRORS", asname=alias)],
                    level=level,
                )
            )
            error_registry_aliases.append(alias)
        # Well-known imports for client-visible scalar-like types used in param and simple return annotations
        wk_client: set[str] = set()
        for _path, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef) and p.type.kind == "well_known":
                    wk_client.add(p.type.name)
            if isinstance(rpc.returns, TypeRef) and rpc.returns.kind == "well_known":
                wk_client.add(rpc.returns.name)
        if wk_client:
            emit_well_known_imports(new_body, wk_client)

        # If any client-visible annotation uses Optional[...] add typing.Optional import
        needs_optional = False
        for _path, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef) and type_has_optional(p.type):
                    needs_optional = True
            if isinstance(rpc.returns, TypeRef) and type_has_optional(rpc.returns):
                needs_optional = True
        if needs_optional:
            new_body.append(
                ast.ImportFrom(
                    module="typing", names=[ast.alias(name="Optional")], level=0
                )
            )
        # If client defines event helpers, import Callable and Awaitable
        has_emit = any(True for _ in iter_emits(svc.service))
        has_listen = any(True for _ in iter_listens(svc.service))
        if has_emit or has_listen:
            new_body.append(
                ast.ImportFrom(
                    module="typing",
                    names=[ast.alias(name="Callable"), ast.alias(name="Awaitable")],
                    level=0,
                )
            )

        # merged error registry for the client instance
        new_body.append(
            ast.Assign(
                targets=[ast.Name(id="MERGED_ERRORS")],
                value=ast.Dict(keys=[], values=[]),
            )
        )
        for alias in error_registry_aliases:
            new_body.append(
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="MERGED_ERRORS"), attr="update"
                        ),
                        args=[ast.Name(id=alias)],
                        keywords=[],
                    )
                )
            )
        # Rebuild client: drop model classes (moved to models.py) and keep only the client class
        # Build a new module AST that prepends imports to the parsed client module code
        # Simpler: write header imports + client_code concatenated (both formatted by Black)
        header = ast.Module(body=new_body, type_ignores=[])
        header_code = format_code(ast.unparse(ast.fix_missing_locations(header)))
        client_code = header_code + "\n" + client_code
        (srv_dir / "client.py").write_text(client_code, encoding="utf-8")
        written.append(srv_dir / "client.py")

        # server.py generation
        server_code = render_server_module(project.subject_prefix, svc.service)

        # Add imports similar to client
        new_server_body: list[ast.stmt] = []
        new_server_body.append(
            ast.ImportFrom(
                module="amirpc", names=[ast.alias(name="BaseServer")], level=0
            )
        )
        new_server_body.append(
            ast.ImportFrom(
                module="abc",
                names=[ast.alias(name="ABC"), ast.alias(name="abstractmethod")],
                level=0,
            )
        )

        # Import request payload and inline result classes for method signatures and _bind_rpc
        payload_result_names: list[str] = []
        for ns_path, r in iter_rpcs(svc.service):
            payload_result_names.append(request_payload_name(svc.service, r, ns_path))
            if isinstance(r.returns, InlineStruct):
                payload_result_names.append(
                    response_result_name(svc.service, r, ns_path)
                )
        # Event payload imports for server (used in annotations and _bind_event)
        from amic.codegen.utils import emit_payload_name, listen_payload_name

        event_payload_names_srv: list[str] = []
        for ns_path, ev in iter_events(svc.service):
            if getattr(ev, "role", None) == "emit":
                event_payload_names_srv.append(
                    emit_payload_name(svc.service, ev, ns_path)
                )
            elif getattr(ev, "role", None) == "listen":
                event_payload_names_srv.append(
                    listen_payload_name(svc.service, ev, ns_path)
                )
        import_names = sorted(set(payload_result_names + event_payload_names_srv))
        if import_names:
            new_server_body.append(
                ast.ImportFrom(
                    module="models",
                    names=[ast.alias(name=n) for n in import_names],
                    level=1,
                )
            )

        # Compute direct model imports needed for server method annotations (exclude inline result internals and events)
        direct_type_names: set[str] = set()
        for _p, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef):
                    # Extract inner models from complex types (e.g., list[Model], Optional[Model])
                    inner_models = model_types_in(p.type)
                    if inner_models:
                        direct_type_names.update(m.name for m in inner_models)
                    elif p.type.kind not in {"builtin", "well_known"}:
                        direct_type_names.add(p.type.name)
            if isinstance(rpc.returns, TypeRef):
                # Extract inner models from complex return types (e.g., list[DialogInfo])
                inner_models = model_types_in(rpc.returns)
                if inner_models:
                    direct_type_names.update(m.name for m in inner_models)
                elif rpc.returns.kind not in {"builtin", "well_known"}:
                    direct_type_names.add(rpc.returns.name)

        # Local service models (non-domain) for server annotations
        local_model_names = {m.name for m in (svc.non_domain_models or [])}
        server_local_needed = sorted(
            n for n in direct_type_names if n in local_model_names
        )
        domain_names = {m.name for m in (project.domain_models or [])}
        server_domain_needed = sorted(n for n in direct_type_names if n in domain_names)
        server_external_needed_by_module: dict[str, list[str]] = {}
        for n in sorted(direct_type_names):
            if n in local_model_names or n in domain_names:
                continue
            mod = svc.imported_model_modules.get(n)
            if mod and mod != "__DOMAIN__":
                server_external_needed_by_module.setdefault(mod, []).append(n)

        # Domain models imports from parent directory
        if server_domain_needed:
            new_server_body.append(
                ast.ImportFrom(
                    module="models",
                    names=[
                        ast.alias(name=n) for n in sorted(set(server_domain_needed))
                    ],
                    level=2,
                )
            )
        # Enums imports (prefer local)
        direct_enum_names: set[str] = set()
        for _p, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef) and p.type.kind == "enum":
                    direct_enum_names.add(p.type.name)
            if isinstance(rpc.returns, TypeRef) and rpc.returns.kind == "enum":
                direct_enum_names.add(rpc.returns.name)
        local_enum_names = {e.name for e in (getattr(svc, "local_enums", []) or [])}
        domain_enum_names = {
            e.name for e in (getattr(project, "domain_enums", []) or [])
        }
        server_local_enums_needed = sorted(direct_enum_names & local_enum_names)
        server_domain_enums_needed = sorted(
            (direct_enum_names - set(local_enum_names)) & domain_enum_names
        )
        if server_local_enums_needed:
            new_server_body.append(
                ast.ImportFrom(
                    module="enums",
                    names=[ast.alias(name=n) for n in server_local_enums_needed],
                    level=1,
                )
            )
        if server_domain_enums_needed:
            new_server_body.append(
                ast.ImportFrom(
                    module="enums",
                    names=[ast.alias(name=n) for n in server_domain_enums_needed],
                    level=2,
                )
            )

        # Local service models imports - import all local models for annotations
        # (direct_type_names may miss references in inline structs or nested types)
        if local_model_names:
            new_server_body.append(
                ast.ImportFrom(
                    module="models",
                    names=[ast.alias(name=n) for n in sorted(local_model_names)],
                    level=1,
                )
            )

        # Well-known imports for server annotations
        wk_server: set[str] = set()
        for _path, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef) and p.type.kind == "well_known":
                    wk_server.add(p.type.name)
            if isinstance(rpc.returns, TypeRef) and rpc.returns.kind == "well_known":
                wk_server.add(rpc.returns.name)
        for _path, ev in iter_events(svc.service):
            for p in ev.params:
                if isinstance(p.type, TypeRef) and p.type.kind == "well_known":
                    wk_server.add(p.type.name)
        if wk_server:
            emit_well_known_imports(new_server_body, wk_server)

        # If any server annotation uses Optional[...] add typing.Optional import
        server_needs_optional = False
        for _path, rpc in iter_rpcs(svc.service):
            for p in rpc.params:
                if isinstance(p.type, TypeRef) and type_has_optional(p.type):
                    server_needs_optional = True
            if isinstance(rpc.returns, TypeRef) and type_has_optional(rpc.returns):
                server_needs_optional = True
        if server_needs_optional:
            new_server_body.append(
                ast.ImportFrom(
                    module="typing", names=[ast.alias(name="Optional")], level=0
                )
            )

        # External model imports
        for mod_path, names in sorted(server_external_needed_by_module.items()):
            module_name, level = resolve_import_module(svc.module, mod_path, "models")
            # server context is one level deeper than client header; adjust: same logic works (wheel paths identical)
            new_server_body.append(
                ast.ImportFrom(
                    module=module_name,
                    names=[ast.alias(name=n) for n in sorted(set(names))],
                    level=level,
                )
            )

        header_srv = ast.Module(body=new_server_body, type_ignores=[])
        server_code = (
            format_code(ast.unparse(ast.fix_missing_locations(header_srv)))
            + "\n"
            + server_code
        )
        (srv_dir / "server.py").write_text(server_code, encoding="utf-8")
        written.append(srv_dir / "server.py")

        # events.py for service: publisher class and subject constants for emit events
        events_code = render_events_module(project.subject_prefix, svc.service)
        (srv_dir / "events.py").write_text(events_code, encoding="utf-8")
        written.append(srv_dir / "events.py")

    return written

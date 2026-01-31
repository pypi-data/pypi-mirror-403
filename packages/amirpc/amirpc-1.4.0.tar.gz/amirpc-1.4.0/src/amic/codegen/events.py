"""Events module code generation: ServiceEmitter and namespace emitters.

Generates `<service>/events.py` containing:
- <ServiceName>Emitter class with async emit_<event>(...) methods for root emits
- Nested <ServiceName><Ns>Emitter classes for namespaced emits, exposed as attributes

Notes:
- Subjects are embedded as literals (consistent with server generation).
- Generated code uses relative imports for local models and absolute import for runtime helper.
"""

import ast
from collections.abc import Iterable

from amic.ast.model import Event, Namespace, Service
from amic.codegen.emit import format_code
from amic.codegen.utils import snake, subject_for_emit


def _iter_ns(ns: Namespace, prefix: list[str]) -> Iterable[tuple[list[str], object]]:
    current = [*prefix, snake(ns.name)]
    for it in getattr(ns, "items", []) or []:
        if isinstance(it, Event):
            yield current, it
        elif isinstance(it, Namespace):
            yield from _iter_ns(it, current)


def _iter_emits(service: Service) -> Iterable[tuple[list[str], Event]]:
    for e in getattr(service, "emits", []) or []:
        yield [], e
    for ns in getattr(service, "namespaces", []) or []:
        for path, it in _iter_ns(ns, []):
            if isinstance(it, Event) and getattr(it, "role", None) == "emit":
                yield path, it


def _ns_class_name(service_name: str, ns_path: list[str]) -> str:
    parts = [service_name] + [seg.capitalize() for seg in "_".join(ns_path).split("_")]
    return "".join(parts) + "Emitter"


def _event_payload_name(ev: Event, ns_path: list[str] | None = None) -> str:
    ev_pascal = "".join(seg.capitalize() for seg in snake(ev.name).split("_"))
    if ns_path:
        prefix = "".join(seg.capitalize() for seg in "_".join(ns_path).split("_"))
        return f"{prefix}{ev_pascal}EmitEvent"
    return f"{ev_pascal}EmitEvent"


def build_events_module_ast(subject_prefix: str, service: Service) -> ast.Module:
    body: list[ast.stmt] = []

    # Header imports
    body.append(
        ast.ImportFrom(
            module="amirpc",
            names=[ast.alias(name="BaseEmitter"), ast.alias(name="Runtime")],
            level=0,
        )
    )
    body.append(ast.ImportFrom(module="uuid", names=[ast.alias(name="UUID")], level=0))

    # Import payload models for emits
    emit_payloads: list[str] = []
    for ns_path, ev in _iter_emits(service):
        emit_payloads.append(_event_payload_name(ev, ns_path))
    if emit_payloads:
        body.append(
            ast.ImportFrom(
                module="models",
                names=[ast.alias(name=n) for n in sorted(set(emit_payloads))],
                level=1,
            )
        )

    # Build namespace class map
    ns_paths: list[list[str]] = []
    for ns_path, _ev in _iter_emits(service):
        for i in range(1, len(ns_path) + 1):
            p = ns_path[:i]
            if p not in ns_paths:
                ns_paths.append(p)

    # Root emitter class
    root_body: list[ast.stmt] = []

    # If there are namespaced emitters, create __init__ to instantiate them
    top_level_ns = sorted({p[0] for p in ns_paths if len(p) >= 1})
    if top_level_ns:
        init_body: list[ast.stmt] = [
            # super().__init__(nc=nc)
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Call(func=ast.Name(id="super"), args=[], keywords=[]),
                        attr="__init__",
                    ),
                    args=[],
                    keywords=[ast.keyword(arg="runtime", value=ast.Name(id="runtime"))],
                )
            ),
        ]
        for top in top_level_ns:
            cls_name = _ns_class_name(service.name, [top])
            init_body.append(
                ast.Assign(
                    targets=[ast.Attribute(value=ast.Name(id="self"), attr=top)],
                    value=ast.Call(
                        func=ast.Name(id=cls_name),
                        args=[],
                        keywords=[
                            ast.keyword(arg="runtime", value=ast.Name(id="runtime"))
                        ],
                    ),
                )
            )
        root_body.append(
            ast.FunctionDef(
                name="__init__",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="self")],
                    vararg=None,
                    kwonlyargs=[
                        ast.arg(arg="runtime", annotation=ast.Name(id="Runtime"))
                    ],
                    kw_defaults=[None],
                    defaults=[],
                ),
                body=init_body,
                decorator_list=[],
                returns=None,
            )
        )

    # emit methods on root (ns_path == [])
    for ns_path, ev in _iter_emits(service):
        if ns_path:
            continue
        method_name = "emit_" + snake(ev.name)
        args = ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(arg="self"),
                ast.arg(
                    arg="payload",
                    annotation=ast.Name(id=_event_payload_name(ev, ns_path)),
                ),
            ],
            vararg=None,
            kwonlyargs=[
                ast.arg(
                    arg="source",
                    annotation=ast.BinOp(
                        left=ast.Name(id="str"),
                        op=ast.BitOr(),
                        right=ast.Name(id="None"),
                    ),
                ),
                ast.arg(
                    arg="event_id",
                    annotation=ast.BinOp(
                        left=ast.Name(id="UUID"),
                        op=ast.BitOr(),
                        right=ast.Name(id="None"),
                    ),
                ),
            ],
            kw_defaults=[ast.Constant(value=None), ast.Constant(value=None)],
            defaults=[],
        )
        subject_literal = subject_for_emit(
            subject_prefix, service.name, ns_path, ev.name
        )
        body_stmt = ast.Return(
            value=ast.Await(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="self"), attr="_publish_event"
                    ),
                    args=[
                        ast.Constant(value=subject_literal),
                        ast.Name(id="payload"),
                    ],
                    keywords=[
                        ast.keyword(arg="source", value=ast.Name(id="source")),
                        ast.keyword(arg="event_id", value=ast.Name(id="event_id")),
                    ],
                )
            )
        )
        root_body.append(
            ast.AsyncFunctionDef(
                name=method_name,
                args=args,
                body=[body_stmt],
                decorator_list=[],
                returns=ast.Name(id="None"),
            )
        )

    # Ensure non-empty class body
    if not root_body:
        root_body = [ast.Pass()]

    body.append(
        ast.ClassDef(
            name=f"{service.name}Emitter",
            bases=[ast.Name(id="BaseEmitter")],
            keywords=[],
            body=root_body,
            decorator_list=[],
        )
    )

    # Build nested namespace emitter classes (for each ns_path)
    for path in sorted(ns_paths, key=lambda p: (len(p), p)):
        cls_name = _ns_class_name(service.name, path)

        class_body: list[ast.stmt] = []

        # Check if there are child namespaces to instantiate
        children = sorted(
            {
                p[len(path)]
                for p in ns_paths
                if len(p) > len(path) and p[: len(path)] == path
            }
        )
        if children:
            init_body = [
                # super().__init__(nc=nc)
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Call(
                                func=ast.Name(id="super"), args=[], keywords=[]
                            ),
                            attr="__init__",
                        ),
                        args=[],
                        keywords=[
                            ast.keyword(arg="runtime", value=ast.Name(id="runtime"))
                        ],
                    )
                ),
            ]
            for child in children:
                child_cls = _ns_class_name(service.name, [*path, child])
                init_body.append(
                    ast.Assign(
                        targets=[ast.Attribute(value=ast.Name(id="self"), attr=child)],
                        value=ast.Call(
                            func=ast.Name(id=child_cls),
                            args=[],
                            keywords=[
                                ast.keyword(arg="runtime", value=ast.Name(id="runtime"))
                            ],
                        ),
                    )
                )
            class_body.append(
                ast.FunctionDef(
                    name="__init__",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="self")],
                        vararg=None,
                        kwonlyargs=[
                            ast.arg(arg="runtime", annotation=ast.Name(id="Runtime"))
                        ],
                        kw_defaults=[None],
                        defaults=[],
                    ),
                    body=init_body,
                    decorator_list=[],
                    returns=None,
                )
            )

        # emit methods for events exactly at this path
        for ns_path, ev in _iter_emits(service):
            if ns_path != path:
                continue
            method_name = "emit_" + snake(ev.name)
            args = ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg(arg="self"),
                    ast.arg(
                        arg="payload",
                        annotation=ast.Name(id=_event_payload_name(ev, ns_path)),
                    ),
                ],
                vararg=None,
                kwonlyargs=[
                    ast.arg(
                        arg="source",
                        annotation=ast.BinOp(
                            left=ast.Name(id="str"),
                            op=ast.BitOr(),
                            right=ast.Name(id="None"),
                        ),
                    ),
                    ast.arg(
                        arg="event_id",
                        annotation=ast.BinOp(
                            left=ast.Name(id="UUID"),
                            op=ast.BitOr(),
                            right=ast.Name(id="None"),
                        ),
                    ),
                ],
                kw_defaults=[ast.Constant(value=None), ast.Constant(value=None)],
                defaults=[],
            )
            subject_literal = subject_for_emit(
                subject_prefix, service.name, ns_path, ev.name
            )
            body_stmt = ast.Return(
                value=ast.Await(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="self"), attr="_publish_event"
                        ),
                        args=[
                            ast.Constant(value=subject_literal),
                            ast.Name(id="payload"),
                        ],
                        keywords=[
                            ast.keyword(arg="source", value=ast.Name(id="source")),
                            ast.keyword(arg="event_id", value=ast.Name(id="event_id")),
                        ],
                    )
                )
            )
            class_body.append(
                ast.AsyncFunctionDef(
                    name=method_name,
                    args=args,
                    body=[body_stmt],
                    decorator_list=[],
                    returns=ast.Name(id="None"),
                )
            )

        # Ensure non-empty class body
        if not class_body:
            class_body = [ast.Pass()]

        body.append(
            ast.ClassDef(
                name=cls_name,
                bases=[ast.Name(id="BaseEmitter")],
                keywords=[],
                body=class_body,
                decorator_list=[],
            )
        )

    return ast.Module(body=body, type_ignores=[])


def render_events_module(subject_prefix: str, service: Service) -> str:
    return format_code(
        ast.unparse(
            ast.fix_missing_locations(build_events_module_ast(subject_prefix, service))
        )
    )

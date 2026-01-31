"""Client classes code generation."""

import ast

from amic.ast.model import InlineStruct, Service, TypeRef
from amic.codegen.emit import format_code
from amic.codegen.utils import (
    emit_payload_name,
    iter_emits,
    iter_listens,
    iter_rpcs,
    listen_payload_name,
    py_type,
    request_payload_name,
    response_result_name,
    snake,
    subject_for_emit,
    subject_for_listen,
    subject_for_rpc,
    type_expr,
)


def build_client_module_ast(subject_prefix: str, service: Service) -> ast.Module:
    # This module intentionally contains only class definitions; imports are handled by the caller.
    body: list[ast.stmt] = []
    client_body: list[ast.stmt] = []

    def _is_targeted_rpc(rpc) -> bool:
        for a in getattr(rpc, "attrs", []) or []:
            if a.name == "targeted":
                return True
        return False

    for ns_path, rpc in iter_rpcs(service):
        if ns_path:
            continue
        fn_name = snake(rpc.name)
        args = [ast.arg(arg="self")]
        for p in rpc.params:
            args.append(ast.arg(arg=p.name, annotation=type_expr(p.type)))
        kwonlyargs: list[ast.arg] = []
        kw_defaults: list[ast.expr | None] = []
        if _is_targeted_rpc(rpc):
            kwonlyargs.append(ast.arg(arg="rpc_target", annotation=ast.Name(id="str")))
            kw_defaults.append(None)
        # Optional RPC timeout (seconds)
        kwonlyargs.append(
            ast.arg(
                arg="rpc_timeout",
                annotation=ast.Name(id="float"),
            )
        )
        kw_defaults.append(ast.Constant(value=5.0))
        if isinstance(rpc.returns, InlineStruct):
            ret_ann = ast.Name(id=response_result_name(service, rpc, ns_path))
            resp_type_expr = ast.Name(id=response_result_name(service, rpc, ns_path))
        else:
            assert isinstance(rpc.returns, TypeRef)
            ret_ann = type_expr(rpc.returns)
            resp_type_expr = type_expr(rpc.returns)
        method_body: list[ast.stmt] = []
        base_subject = subject_for_rpc(subject_prefix, service.name, ns_path, rpc.name)
        req_ctor_keywords = [
            ast.keyword(arg=p.name, value=ast.Name(id=p.name)) for p in rpc.params
        ]
        method_body.append(
            ast.Assign(
                targets=[ast.Name(id="_req")],
                value=ast.Call(
                    func=ast.Name(id=request_payload_name(service, rpc, ns_path)),
                    args=[],
                    keywords=req_ctor_keywords,
                ),
            )
        )
        # Build subject expression (append .{rpc_target} for targeted RPCs)
        if _is_targeted_rpc(rpc):
            subject_expr = ast.JoinedStr(
                values=[
                    ast.Constant(value=base_subject + "."),
                    ast.FormattedValue(value=ast.Name(id="rpc_target"), conversion=-1),
                ]
            )
        else:
            subject_expr = ast.Constant(value=base_subject)
        method_body.append(
            ast.Return(
                value=ast.Await(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="self"), attr="_request_payload"
                        ),
                        args=[
                            subject_expr,
                            ast.Name(id="_req"),
                            resp_type_expr,
                        ],
                        keywords=[
                            ast.keyword(
                                arg="rpc_timeout", value=ast.Name(id="rpc_timeout")
                            )
                        ],
                    )
                )
            )
        )
        # Build docstring with summary + Args/Returns/Raises
        doc_lines: list[str] = []
        if getattr(rpc, "doc", None):
            doc_lines.append(str(rpc.doc).strip())
        # Args
        if rpc.params:
            doc_lines.append("")
            doc_lines.append("Args:")
            for p in rpc.params:
                p_doc = (p.doc or "").splitlines()[0] if getattr(p, "doc", None) else ""
                doc_lines.append(
                    f"    {p.name} ({py_type(p.type)}): {p_doc}"
                    if p_doc
                    else f"    {p.name} ({py_type(p.type)}):"
                )
        if _is_targeted_rpc(rpc):
            if not rpc.params:
                doc_lines.append("")
                doc_lines.append("Args:")
            doc_lines.append(
                "    rpc_target (str): Target instance identifier for direct addressing"
            )
        # Transport options under Args
        if not rpc.params and not _is_targeted_rpc(rpc):
            doc_lines.append("")
            doc_lines.append("Args:")
        doc_lines.append(
            "    rpc_timeout (float): Request timeout in seconds (default: 5.0)"
        )
        # Returns
        if isinstance(rpc.returns, InlineStruct):
            doc_lines.append("")
            doc_lines.append("Returns:")
            doc_lines.append(
                f"    {response_result_name(service, rpc, ns_path)}: Inline result"
            )
        else:
            doc_lines.append("")
            doc_lines.append("Returns:")
            doc_lines.append(f"    {py_type(rpc.returns)}: Result")
        # Raises from @throws attribute if any
        throws = []
        for a in rpc.attrs:
            if a.name == "throws":
                throws.extend([str(x) for x in a.args])
        if throws:
            doc_lines.append("")
            doc_lines.append("Raises:")
            for en in throws:
                doc_lines.append(f"    {en}:")

        method_body_with_doc = method_body
        if doc_lines:
            method_body_with_doc = [
                ast.Expr(value=ast.Constant(value="\n".join(doc_lines)))
            ] + method_body

        client_body.append(
            ast.AsyncFunctionDef(
                name=fn_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=args,
                    vararg=None,
                    kwonlyargs=kwonlyargs,
                    kw_defaults=kw_defaults,
                    defaults=[],
                ),
                body=method_body_with_doc,
                decorator_list=[],
                returns=ret_ann,
            )
        )

    # Root-level event helpers
    # Emits -> subscription methods: on_<event>
    for ns_path, ev in iter_emits(service):
        if ns_path:
            continue
        fn_name = "on_" + snake(ev.name)
        payload_cls = ast.Name(id=emit_payload_name(service, ev, ns_path))
        args = [
            ast.arg(arg="self"),
            ast.arg(
                arg="handler",
                annotation=ast.Subscript(
                    value=ast.Name(id="Callable"),
                    slice=ast.Tuple(
                        elts=[
                            ast.List(elts=[payload_cls], ctx=ast.Load()),
                            ast.Subscript(
                                value=ast.Name(id="Awaitable"),
                                slice=ast.Constant(value=None),
                                ctx=ast.Load(),
                            ),
                        ],
                        ctx=ast.Load(),
                    ),
                    ctx=ast.Load(),
                ),
            ),
        ]
        method_body = [
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="self"), attr="_subscribe_event"
                    ),
                    args=[
                        ast.Constant(
                            value=subject_for_emit(
                                subject_prefix, service.name, ns_path or [], ev.name
                            )
                        ),
                        payload_cls,
                        ast.Name(id="handler"),
                    ],
                    keywords=[
                        ast.keyword(arg="queue", value=ast.Name(id="queue")),
                    ],
                )
            )
        ]
        client_body.append(
            ast.FunctionDef(
                name=fn_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=args,
                    vararg=None,
                    kwonlyargs=[
                        ast.arg(
                            arg="queue",
                            annotation=ast.BinOp(
                                left=ast.Name(id="str"),
                                op=ast.BitOr(),
                                right=ast.Constant(value=None),
                            ),
                        ),
                    ],
                    kw_defaults=[ast.Constant(value=None)],
                    defaults=[],
                ),
                body=method_body,
                decorator_list=[],
                returns=None,
            )
        )

    # Listens -> publish methods: publish_<event>
    for ns_path, ev in iter_listens(service):
        if ns_path:
            continue
        fn_name = "publish_" + snake(ev.name)
        payload_cls = ast.Name(id=listen_payload_name(service, ev, ns_path))
        args = [ast.arg(arg="self"), ast.arg(arg="payload", annotation=payload_cls)]
        method_body = [
            ast.Return(
                value=ast.Await(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="self"), attr="_publish_event"
                        ),
                        args=[
                            ast.Constant(
                                value=subject_for_listen(
                                    subject_prefix, service.name, ns_path or [], ev.name
                                )
                            ),
                            ast.Name(id="payload"),
                        ],
                        keywords=[],
                    )
                )
            )
        ]
        client_body.append(
            ast.AsyncFunctionDef(
                name=fn_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=args,
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=method_body,
                decorator_list=[],
                returns=None,
            )
        )

    for ns in getattr(service, "namespaces", []) or []:
        sub_body: list[ast.stmt] = []
        for ns_path, rpc in iter_rpcs(service):
            if not ns_path or ns_path[0] != snake(ns.name):
                continue
            fn_name = snake(rpc.name)
            args = [ast.arg(arg="self")]
            for p in rpc.params:
                args.append(ast.arg(arg=p.name, annotation=type_expr(p.type)))
            kwonlyargs: list[ast.arg] = []
            kw_defaults: list[ast.expr | None] = []
            if _is_targeted_rpc(rpc):
                kwonlyargs.append(
                    ast.arg(arg="rpc_target", annotation=ast.Name(id="str"))
                )
                kw_defaults.append(None)
            # Optional RPC timeout (seconds)
            kwonlyargs.append(
                ast.arg(
                    arg="rpc_timeout",
                    annotation=ast.Name(id="float"),
                )
            )
            kw_defaults.append(ast.Constant(value=5.0))
            if isinstance(rpc.returns, InlineStruct):
                ret_ann = ast.Name(id=response_result_name(service, rpc, ns_path))
                resp_type_expr = ast.Name(
                    id=response_result_name(service, rpc, ns_path)
                )
            else:
                assert isinstance(rpc.returns, TypeRef)
                ret_ann = type_expr(rpc.returns)
                resp_type_expr = type_expr(rpc.returns)
            req_ctor_keywords = [
                ast.keyword(arg=p.name, value=ast.Name(id=p.name)) for p in rpc.params
            ]
            base_subject = subject_for_rpc(
                subject_prefix, service.name, ns_path, rpc.name
            )
            method_body = [
                ast.Assign(
                    targets=[ast.Name(id="_req")],
                    value=ast.Call(
                        func=ast.Name(id=request_payload_name(service, rpc, ns_path)),
                        args=[],
                        keywords=req_ctor_keywords,
                    ),
                ),
            ]
            if _is_targeted_rpc(rpc):
                subject_expr = ast.JoinedStr(
                    values=[
                        ast.Constant(value=base_subject + "."),
                        ast.FormattedValue(
                            value=ast.Name(id="rpc_target"), conversion=-1
                        ),
                    ]
                )
            else:
                subject_expr = ast.Constant(value=base_subject)
            method_body.append(
                ast.Return(
                    value=ast.Await(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="self"), attr="_request_payload"
                            ),
                            args=[subject_expr, ast.Name(id="_req"), resp_type_expr],
                            keywords=[
                                ast.keyword(
                                    arg="rpc_timeout", value=ast.Name(id="rpc_timeout")
                                )
                            ],
                        )
                    )
                )
            )
            # Docstring for namespaced RPCs
            doc_lines = []
            if getattr(rpc, "doc", None):
                doc_lines.append(str(rpc.doc).strip())
            if rpc.params:
                doc_lines.append("")
                doc_lines.append("Args:")
                for p in rpc.params:
                    p_doc = (
                        (p.doc or "").splitlines()[0] if getattr(p, "doc", None) else ""
                    )
                    doc_lines.append(
                        f"    {p.name} ({py_type(p.type)}): {p_doc}"
                        if p_doc
                        else f"    {p.name} ({py_type(p.type)}):"
                    )
            if _is_targeted_rpc(rpc):
                if not rpc.params:
                    doc_lines.append("")
                    doc_lines.append("Args:")
                doc_lines.append(
                    "    rpc_target (str): Target instance identifier for direct addressing"
                )
            # Transport options under Args
            if not rpc.params and not _is_targeted_rpc(rpc):
                doc_lines.append("")
                doc_lines.append("Args:")
            doc_lines.append(
                "    rpc_timeout (float): Request timeout in seconds (default: 5.0)"
            )
            if isinstance(rpc.returns, InlineStruct):
                doc_lines.append("")
                doc_lines.append("Returns:")
                doc_lines.append(
                    f"    {response_result_name(service, rpc, ns_path)}: Inline result"
                )
            else:
                doc_lines.append("")
                doc_lines.append("Returns:")
                doc_lines.append(f"    {py_type(rpc.returns)}: Result")
            throws = []
            for a in rpc.attrs:
                if a.name == "throws":
                    throws.extend([str(x) for x in a.args])
            if throws:
                doc_lines.append("")
                doc_lines.append("Raises:")
                for en in throws:
                    doc_lines.append(f"    {en}:")

            method_body_ns = method_body
            if doc_lines:
                method_body_ns = [
                    ast.Expr(value=ast.Constant(value="\n".join(doc_lines)))
                ] + method_body
            sub_body.append(
                ast.AsyncFunctionDef(
                    name=fn_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=args,
                        vararg=None,
                        kwonlyargs=kwonlyargs,
                        kw_defaults=kw_defaults,
                        defaults=[],
                    ),
                    body=method_body_ns,
                    decorator_list=[],
                    returns=ret_ann,
                )
            )
        # Namespace events
        for ns_path, ev in iter_emits(service):
            if not ns_path or ns_path[0] != snake(ns.name):
                continue
            fn_name = "on_" + snake(ev.name)
            payload_cls = ast.Name(id=emit_payload_name(service, ev, ns_path))
            args = [
                ast.arg(arg="self"),
                ast.arg(
                    arg="handler",
                    annotation=ast.Subscript(
                        value=ast.Name(id="Callable"),
                        slice=ast.Tuple(
                            elts=[
                                ast.List(elts=[payload_cls], ctx=ast.Load()),
                                ast.Subscript(
                                    value=ast.Name(id="Awaitable"),
                                    slice=ast.Constant(value=None),
                                    ctx=ast.Load(),
                                ),
                            ],
                            ctx=ast.Load(),
                        ),
                        ctx=ast.Load(),
                    ),
                ),
            ]
            method_body = [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="self"), attr="_subscribe_event"
                        ),
                        args=[
                            ast.Constant(
                                value=subject_for_emit(
                                    subject_prefix, service.name, ns_path, ev.name
                                )
                            ),
                            payload_cls,
                            ast.Name(id="handler"),
                        ],
                        keywords=[
                            ast.keyword(arg="queue", value=ast.Name(id="queue")),
                        ],
                    )
                )
            ]
            sub_body.append(
                ast.FunctionDef(
                    name=fn_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=args,
                        vararg=None,
                        kwonlyargs=[
                            ast.arg(
                                arg="queue",
                                annotation=ast.BinOp(
                                    left=ast.Name(id="str"),
                                    op=ast.BitOr(),
                                    right=ast.Constant(value=None),
                                ),
                            ),
                        ],
                        kw_defaults=[ast.Constant(value=None)],
                        defaults=[],
                    ),
                    body=method_body,
                    decorator_list=[],
                    returns=None,
                )
            )
        for ns_path, ev in iter_listens(service):
            if not ns_path or ns_path[0] != snake(ns.name):
                continue
            fn_name = "publish_" + snake(ev.name)
            payload_cls = ast.Name(id=listen_payload_name(service, ev, ns_path))
            args = [ast.arg(arg="self"), ast.arg(arg="payload", annotation=payload_cls)]
            method_body = [
                ast.Return(
                    value=ast.Await(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="self"), attr="_publish_event"
                            ),
                            args=[
                                ast.Constant(
                                    value=subject_for_listen(
                                        subject_prefix, service.name, ns_path, ev.name
                                    )
                                ),
                                ast.Name(id="payload"),
                            ],
                            keywords=[],
                        )
                    )
                )
            ]
            sub_body.append(
                ast.AsyncFunctionDef(
                    name=fn_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=args,
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=method_body,
                    decorator_list=[],
                    returns=None,
                )
            )
        # Ensure non-empty class body
        if not sub_body:
            sub_body = [ast.Pass()]
        # Initialize common errors registry and subject prefix at class level for namespace clients
        full_prefix = f"{subject_prefix}.{snake(service.name)}"
        sub_body.insert(
            0,
            ast.Assign(
                targets=[ast.Name(id="_subject_prefix")],
                value=ast.Constant(value=full_prefix),
            ),
        )
        sub_body.insert(
            0,
            ast.Assign(
                targets=[ast.Name(id="_errors_registry")],
                value=ast.Name(id="MERGED_ERRORS"),
            ),
        )
        body.append(
            ast.ClassDef(
                name=f"{service.name}{ns.name}Client",
                bases=[ast.Name(id="BaseClient")],
                keywords=[],
                body=sub_body,
                decorator_list=[],
            )
        )

    # Ensure root client class has non-empty body
    if not client_body:
        client_body = [ast.Pass()]
    # Build __init__ to initialize namespace client attributes and bind merged error registry
    init_body: list[ast.stmt] = []
    # super().__init__(runtime=runtime)
    init_body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Call(func=ast.Name(id="super"), args=[], keywords=[]),
                    attr="__init__",
                ),
                args=[],
                keywords=[ast.keyword(arg="runtime", value=ast.Name(id="runtime"))],
            )
        )
    )
    # Note: _errors_registry will be set as a class attribute on the root client
    # Initialize namespace attributes
    for ns in getattr(service, "namespaces", []) or []:
        ns_attr = snake(ns.name)
        ns_cls = f"{service.name}{ns.name}Client"
        init_body.append(
            ast.Assign(
                targets=[ast.Attribute(value=ast.Name(id="self"), attr=ns_attr)],
                value=ast.Call(
                    func=ast.Name(id=ns_cls),
                    args=[],
                    keywords=[ast.keyword(arg="runtime", value=ast.Name(id="runtime"))],
                ),
            )
        )
    # Add type comments to help users and static analyzers
    init_fn = ast.FunctionDef(
        name="__init__",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="self")],
            vararg=None,
            kwonlyargs=[ast.arg(arg="runtime", annotation=ast.Name(id="Runtime"))],
            kw_defaults=[None],
            defaults=[],
        ),
        body=init_body,
        decorator_list=[],
        returns=None,
    )

    root_client_body = [init_fn] + (client_body or [])
    if not root_client_body:
        root_client_body = [ast.Pass()]

    # Root client class with namespace attributes typed
    class_body = []
    # Add _subject_prefix for health check
    full_prefix = f"{subject_prefix}.{snake(service.name)}"
    class_body.append(
        ast.Assign(
            targets=[ast.Name(id="_subject_prefix")],
            value=ast.Constant(value=full_prefix),
        )
    )
    # Add typed namespace attributes: tokens: AuthTokensClient
    for ns in getattr(service, "namespaces", []) or []:
        ns_attr = snake(ns.name)
        ns_cls = f"{service.name}{ns.name}Client"
        class_body.append(
            ast.AnnAssign(
                target=ast.Name(id=ns_attr, ctx=ast.Store()),
                annotation=ast.Name(id=ns_cls),
                value=None,
                simple=1,
            )
        )
    # Initialize common errors registry at class level
    class_body.append(
        ast.Assign(
            targets=[ast.Name(id="_errors_registry")],
            value=ast.Name(id="MERGED_ERRORS"),
        )
    )
    class_body.extend(root_client_body)
    body.append(
        ast.ClassDef(
            name=f"{service.name}Client",
            bases=[ast.Name(id="BaseClient")],
            keywords=[],
            body=class_body,
            decorator_list=[],
        )
    )
    return ast.Module(body=body, type_ignores=[])


def render_client_module(subject_prefix: str, service: Service) -> str:
    return format_code(
        ast.unparse(
            ast.fix_missing_locations(build_client_module_ast(subject_prefix, service))
        )
    )

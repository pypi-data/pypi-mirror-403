"""Server ABCs and binding code generation."""

import ast

from amic.ast.model import InlineStruct, Service
from amic.codegen.emit import format_code
from amic.codegen.utils import (
    iter_listens,
    iter_rpcs,
    listen_payload_name,
    py_type,
    request_payload_name,
    response_result_name,
    return_annotation_expr,
    snake,
    subject_for_listen,
    subject_for_rpc,
)

# Use snake() from utils


def build_server_module_ast(subject_prefix: str, service: Service) -> ast.Module:
    def _is_targeted_rpc(rpc) -> bool:
        for a in getattr(rpc, "attrs", []) or []:
            if a.name == "targeted":
                return True
        return False

    def build_namespace_abc(ns_name: str, accept_path) -> ast.ClassDef:
        cls_body: list[ast.stmt] = []
        # RPC methods in this namespace
        for ns_path, rpc in iter_rpcs(service):
            if not accept_path(ns_path):
                continue
            method_name = snake(rpc.name)
            args = [
                ast.arg(arg="self"),
                ast.arg(
                    arg="payload",
                    annotation=ast.Name(id=request_payload_name(service, rpc, ns_path)),
                ),
            ]
            ret_ann = return_annotation_expr(service, rpc, ns_path)
            method_body: list[ast.stmt] = []
            # Add docstring with Args/Returns/Raises
            doc_lines: list[str] = []
            if getattr(rpc, "doc", None):
                doc_lines.append(str(rpc.doc).strip())
            # Payload args section
            if rpc.params:
                doc_lines.append("")
                doc_lines.append("Args:")
                doc_lines.append(
                    f"    payload ({request_payload_name(service, rpc, ns_path)}): Request data:"
                )
                for p in rpc.params:
                    p_doc = (
                        (p.doc or "").splitlines()[0] if getattr(p, "doc", None) else ""
                    )
                    doc_lines.append(
                        f"        - {p.name} ({py_type(p.type)}): {p_doc}"
                        if p_doc
                        else f"        - {p.name} ({py_type(p.type)}):"
                    )
            # Returns section
            doc_lines.append("")
            doc_lines.append("Returns:")
            if isinstance(rpc.returns, InlineStruct):
                doc_lines.append(
                    f"    {response_result_name(service, rpc, ns_path)}: Response payload:"
                )
                for f in rpc.returns.fields:
                    f_doc = (
                        (f.doc or "").splitlines()[0] if getattr(f, "doc", None) else ""
                    )
                    doc_lines.append(
                        f"        - {f.name} ({py_type(f.type)}): {f_doc}"
                        if f_doc
                        else f"        - {f.name} ({py_type(f.type)}):"
                    )
            else:
                doc_lines.append(f"    {py_type(rpc.returns)}: Result")
            # Raises
            throws = []
            for a in rpc.attrs:
                if a.name == "throws":
                    throws.extend([str(x) for x in a.args])
            if throws:
                doc_lines.append("")
                doc_lines.append("Raises:")
                for en in throws:
                    doc_lines.append(f"    {en}:")
            method_body.append(ast.Expr(value=ast.Constant(value="\n".join(doc_lines))))
            method_body.append(
                ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="NotImplementedError"),
                        args=[ast.Constant(value="Must be implemented by subclass")],
                        keywords=[],
                    )
                )
            )
            cls_body.append(
                ast.AsyncFunctionDef(
                    name=method_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=args,
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=method_body,
                    decorator_list=[ast.Name(id="abstractmethod")],
                    returns=ret_ann,
                )
            )
        # Listen event handlers in this namespace (on_<event>)
        for ns_path, ev in iter_listens(service):
            if not accept_path(ns_path):
                continue
            method_name = "on_" + snake(ev.name)
            args = [
                ast.arg(arg="self"),
                ast.arg(
                    arg="payload",
                    annotation=ast.Name(id=listen_payload_name(service, ev, ns_path)),
                ),
            ]
            method_body = [
                ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="NotImplementedError"),
                        args=[ast.Constant(value="Must be implemented by subclass")],
                        keywords=[],
                    )
                )
            ]
            cls_body.append(
                ast.AsyncFunctionDef(
                    name=method_name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=args,
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=method_body,
                    decorator_list=[ast.Name(id="abstractmethod")],
                    returns=ast.Name(id="None"),
                )
            )
        return ast.ClassDef(
            name=f"{service.name}{ns_name}Server",
            bases=[ast.Name(id="ABC")],
            keywords=[],
            body=cls_body,
            decorator_list=[],
        )

    # This module intentionally contains only class definitions; imports are handled by the caller.
    body: list[ast.stmt] = []
    for ns in getattr(service, "namespaces", []) or []:
        top = snake(ns.name)
        body.append(
            build_namespace_abc(
                ns.name, lambda path, t=top: (len(path) > 0 and path[0] == t)
            )
        )

    # Root server class with _setup_handlers
    setup_body: list[ast.stmt] = []
    # Call super()._setup_handlers() to register health handler
    setup_body.append(
        ast.Expr(
            ast.Call(
                func=ast.Attribute(
                    value=ast.Call(func=ast.Name(id="super"), args=[], keywords=[]),
                    attr="_setup_handlers",
                ),
                args=[],
                keywords=[],
            )
        )
    )
    # Ensure namespace attributes are instances if classes were assigned at class-level
    for ns in getattr(service, "namespaces", []) or []:
        ns_attr = snake(ns.name)
        setup_body.append(
            ast.If(
                test=ast.Call(
                    func=ast.Name(id="isinstance"),
                    args=[
                        ast.Attribute(value=ast.Name(id="self"), attr=ns_attr),
                        ast.Name(id="type"),
                    ],
                    keywords=[],
                ),
                body=[
                    ast.Assign(
                        targets=[
                            ast.Attribute(value=ast.Name(id="self"), attr=ns_attr)
                        ],
                        value=ast.Call(
                            func=ast.Attribute(value=ast.Name(id="self"), attr=ns_attr),
                            args=[],
                            keywords=[],
                        ),
                    )
                ],
                orelse=[],
            )
        )
    # Bind both root and namespaced RPC
    for ns_path, rpc in iter_rpcs(service):
        method_name = snake(rpc.name)
        subject = subject_for_rpc(subject_prefix, service.name, ns_path, rpc.name)
        # Handler: self.<method> for root; self.<ns>.<method> for namespaced
        if ns_path:
            handler_expr = ast.Attribute(
                value=ast.Attribute(value=ast.Name(id="self"), attr=ns_path[0]),
                attr=method_name,
            )
        else:
            handler_expr = ast.Attribute(value=ast.Name(id="self"), attr=method_name)
        # Build subject expression, appending ".{self.rpc_target}" for targeted RPCs
        if _is_targeted_rpc(rpc):
            subject_expr = ast.JoinedStr(
                values=[
                    ast.Constant(value=subject + "."),
                    ast.FormattedValue(
                        value=ast.Attribute(
                            value=ast.Name(id="self"), attr="rpc_target"
                        ),
                        conversion=-1,
                    ),
                ]
            )
        else:
            subject_expr = ast.Constant(value=subject)
        # Determine response payload type for _bind_rpc
        if isinstance(rpc.returns, InlineStruct):
            response_type_expr = ast.Name(
                id=response_result_name(service, rpc, ns_path)
            )
        elif isinstance(rpc.returns, str):
            response_type_expr = ast.Name(id=rpc.returns)
        elif rpc.returns is not None:
            # TypeRef - convert to Python type string
            response_type_expr = ast.Name(id=py_type(rpc.returns))
        else:
            response_type_expr = ast.Constant(value=None)

        # Queue group name for load balancing: "{prefix}.{service}-rpc"
        queue_name = f"{subject_prefix}.{snake(service.name)}-rpc"
        setup_body.append(
            ast.Expr(
                ast.Call(
                    func=ast.Attribute(value=ast.Name(id="self"), attr="_bind_rpc"),
                    args=[
                        subject_expr,
                        handler_expr,
                        ast.Name(id=request_payload_name(service, rpc, ns_path)),
                        response_type_expr,
                    ],
                    keywords=[
                        ast.keyword(arg="queue", value=ast.Constant(value=queue_name)),
                    ],
                )
            )
        )

    # Bind listen events to handlers
    # Queue group name for load balancing: "{prefix}.{service}-listen"
    listen_queue_name = f"{subject_prefix}.{snake(service.name)}-listen"
    for ns_path, ev in iter_listens(service):
        method_name = "on_" + snake(ev.name)
        subject = subject_for_listen(subject_prefix, service.name, ns_path, ev.name)
        if ns_path:
            handler_expr = ast.Attribute(
                value=ast.Attribute(value=ast.Name(id="self"), attr=ns_path[0]),
                attr=method_name,
            )
        else:
            handler_expr = ast.Attribute(value=ast.Name(id="self"), attr=method_name)
        setup_body.append(
            ast.Expr(
                ast.Call(
                    func=ast.Attribute(value=ast.Name(id="self"), attr="_bind_event"),
                    args=[
                        ast.Constant(value=subject),
                        handler_expr,
                        ast.Name(id=listen_payload_name(service, ev, ns_path)),
                    ],
                    keywords=[
                        ast.keyword(arg="queue", value=ast.Constant(value=listen_queue_name)),
                    ],
                )
            )
        )

    setup_fn = ast.FunctionDef(
        name="_setup_handlers",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="self")],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=setup_body,
        decorator_list=[],
        returns=None,
    )

    # Server class containing namespace attributes (typed as Impl | type[Impl]), _setup_handlers and abstract stubs for root RPCs
    server_body: list[ast.stmt] = []
    # Add _subject_prefix and _service_name for health endpoint
    # e.g., _subject_prefix = "ami.orchestrator"
    full_prefix = f"{subject_prefix}.{snake(service.name)}"
    server_body.append(
        ast.Assign(
            targets=[ast.Name(id="_subject_prefix", ctx=ast.Store())],
            value=ast.Constant(value=full_prefix),
        )
    )
    server_body.append(
        ast.Assign(
            targets=[ast.Name(id="_service_name", ctx=ast.Store())],
            value=ast.Constant(value=snake(service.name)),
        )
    )
    # Add typed namespace attributes at class top: users: AuthUsersServer | type[AuthUsersServer]
    for ns in getattr(service, "namespaces", []) or []:
        ns_attr = snake(ns.name)
        ns_type = f"{service.name}{ns.name}Server"
        union_ann = ast.BinOp(
            left=ast.Name(id=ns_type),
            op=ast.BitOr(),
            right=ast.Subscript(
                value=ast.Name(id="type"), slice=ast.Name(id=ns_type), ctx=ast.Load()
            ),
        )
        server_body.append(
            ast.AnnAssign(
                target=ast.Name(id=ns_attr, ctx=ast.Store()),
                annotation=union_ann,
                value=None,
                simple=1,
            )
        )
    # If any RPC is marked as targeted, require implementors to provide rpc_target
    if any(_is_targeted_rpc(r) for _p, r in iter_rpcs(service)):
        server_body.append(
            ast.FunctionDef(
                name="rpc_target",
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="self")],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[
                    ast.Raise(
                        exc=ast.Call(
                            func=ast.Name(id="NotImplementedError"),
                            args=[
                                ast.Constant(value="Must be implemented by subclass")
                            ],
                            keywords=[],
                        )
                    )
                ],
                decorator_list=[ast.Name(id="property"), ast.Name(id="abstractmethod")],
                returns=ast.Name(id="str"),
            )
        )

    server_body.append(setup_fn)
    for ns_path, rpc in iter_rpcs(service):
        if ns_path:
            continue
        method_name = snake(rpc.name)
        args = [
            ast.arg(arg="self"),
            ast.arg(
                arg="payload",
                annotation=ast.Name(id=request_payload_name(service, rpc, ns_path)),
            ),
        ]
        ret_ann = return_annotation_expr(service, rpc, ns_path)
        # Build doc body similar to namespace methods
        method_body_root: list[ast.stmt] = []
        doc_lines_root: list[str] = []
        if getattr(rpc, "doc", None):
            doc_lines_root.append(str(rpc.doc).strip())
        if rpc.params:
            doc_lines_root.append("")
            doc_lines_root.append("Args:")
            doc_lines_root.append(
                f"    payload ({request_payload_name(service, rpc, ns_path)}): Request data:"
            )
            for p in rpc.params:
                p_doc = (p.doc or "").splitlines()[0] if getattr(p, "doc", None) else ""
                doc_lines_root.append(
                    f"        - {p.name} ({py_type(p.type)}): {p_doc}"
                    if p_doc
                    else f"        - {p.name} ({py_type(p.type)}):"
                )
        doc_lines_root.append("")
        doc_lines_root.append("Returns:")
        if isinstance(rpc.returns, InlineStruct):
            doc_lines_root.append(
                f"    {response_result_name(service, rpc, ns_path)}: Response payload:"
            )
            for f in rpc.returns.fields:
                f_doc = (f.doc or "").splitlines()[0] if getattr(f, "doc", None) else ""
                doc_lines_root.append(
                    f"        - {f.name} ({py_type(f.type)}): {f_doc}"
                    if f_doc
                    else f"        - {f.name} ({py_type(f.type)}):"
                )
        else:
            doc_lines_root.append(f"    {py_type(rpc.returns)}: Result")
        throws_root = []
        for a in rpc.attrs:
            if a.name == "throws":
                throws_root.extend([str(x) for x in a.args])
        if throws_root:
            doc_lines_root.append("")
            doc_lines_root.append("Raises:")
            for en in throws_root:
                doc_lines_root.append(f"    {en}:")
        method_body_root.append(
            ast.Expr(value=ast.Constant(value="\n".join(doc_lines_root)))
        )
        method_body_root.append(
            ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id="NotImplementedError"),
                    args=[ast.Constant(value="Must be implemented by subclass")],
                    keywords=[],
                )
            )
        )
        server_body.append(
            ast.AsyncFunctionDef(
                name=method_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=args,
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=method_body_root,
                decorator_list=[ast.Name(id="abstractmethod")],
                returns=ret_ann,
            )
        )

    # Add abstract listen handlers at root level (with on_ prefix)
    for ns_path, ev in iter_listens(service):
        if ns_path:
            continue
        method_name = "on_" + snake(ev.name)
        args = [
            ast.arg(arg="self"),
            ast.arg(
                arg="payload",
                annotation=ast.Name(id=listen_payload_name(service, ev, ns_path)),
            ),
        ]
        method_body_root: list[ast.stmt] = []
        method_body_root.append(
            ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id="NotImplementedError"),
                    args=[ast.Constant(value="Must be implemented by subclass")],
                    keywords=[],
                )
            )
        )
        server_body.append(
            ast.AsyncFunctionDef(
                name=method_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=args,
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=method_body_root,
                decorator_list=[ast.Name(id="abstractmethod")],
                returns=ast.Name(id="None"),
            )
        )

    body.append(
        ast.ClassDef(
            name=f"{service.name}Server",
            bases=[ast.Name(id="BaseServer"), ast.Name(id="ABC")],
            keywords=[],
            body=server_body,
            decorator_list=[],
        )
    )
    return ast.Module(body=body, type_ignores=[])


def render_server_module(subject_prefix: str, service: Service) -> str:
    return format_code(
        ast.unparse(
            ast.fix_missing_locations(build_server_module_ast(subject_prefix, service))
        )
    )

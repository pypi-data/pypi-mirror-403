from functools import lru_cache
from pathlib import Path
from typing import Any

from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput

from amic.ast.model import (
    AclAction,
    AclRule,
    Attribute,
    Decorator,
    EnumDecl,
    EnumMember,
    ErrorDecl,
    Event,
    ImportItem,
    ImportStmt,
    Infrastructure,
    InfrastructureFile,
    InlineStruct,
    Model,
    ModelField,
    ModuleFile,
    Namespace,
    Param,
    ReturnField,
    Rpc,
    Service,
    ServiceLink,
    Spec,
    TypeRef,
)
from amic.errors import AmiToolParseError as AmiParseError

GRAMMAR_PATH = Path(__file__).resolve().parent.parent / "grammar.lark"


@lru_cache(maxsize=1)
def _load_parser() -> Lark:
    with open(GRAMMAR_PATH, encoding="utf-8") as f:
        grammar = f.read()
    return Lark(grammar, start="start", parser="lalr", maybe_placeholders=False)


class ToAst(Transformer):
    def opt_q(self, items):
        # Normalize optional marker: return '?' if present, else None
        return "?" if items else None

    def DOC_LINE(self, token):
        return str(token)[3:].strip()

    def DOC_BLOCK(self, token):
        text = str(token)
        # strip /** */ and leading *
        inner = text[3:-2]
        lines: list[str] = []
        for raw_line in inner.splitlines():
            stripped_line = raw_line.strip()
            if stripped_line.startswith("*"):
                stripped_line = stripped_line[1:].lstrip()
            lines.append(stripped_line)
        return "\n".join([line for line in lines]).strip()

    def doc_comment(self, items):
        # Return tagged tuple to distinguish from CNAME strings
        # ("__doc__", full_text)
        if not items:
            return ("__doc__", "")
        if len(items) == 1:
            return ("__doc__", str(items[0]))
        return ("__doc__", "\n".join(str(x) for x in items if str(x)))

    def STRING(self, token):
        return token[1:-1]

    def CNAME(self, token):
        return str(token)

    def TYPE(self, token):
        name = str(token)
        return TypeRef(name=name, kind="builtin")

    def DOTTED_NAME(self, token):
        return str(token)

    def enum_base(self, items):
        # rule passthrough; returns token text
        return str(items[0]) if items else "string"

    def TRUE(self, _):
        return True

    def FALSE(self, _):
        return False

    def NUMBER(self, token):
        text = str(token)
        try:
            if any(ch in text for ch in [".", "e", "E"]):
                return float(text)
            return int(text)
        except ValueError:
            return float(text)

    def domain_kw(self, _):
        return "domain"

    def attr_value(self, items):
        return items[0]

    def type(self, items):
        # items: [TYPE|CNAME|DOTTED_NAME|list_type, opt_q?]
        t = items[0]
        is_optional = False
        if len(items) > 1:
            # opt_q returns '?' or empty; lark transformer passes literal token or None
            maybe = items[1]
            is_optional = str(maybe) == "?"
        if isinstance(t, TypeRef):
            if is_optional:
                return TypeRef(
                    name=t.name,
                    kind=t.kind,
                    namespace=t.namespace,
                    absolute_id=t.absolute_id,
                    is_domain=t.is_domain,
                    args=t.args,
                    optional=True,
                )
            return t
        name = str(t)
        if name in {"int", "string", "bool", "float"}:
            return TypeRef(name=name, kind="builtin", optional=is_optional)
        return TypeRef(name=name, kind="unresolved", optional=is_optional)

    def list_type(self, items):
        # items: [inner_type]
        inner = items[0]
        if not isinstance(inner, TypeRef):
            # normalize to unresolved TypeRef if parser produced raw token
            inner = TypeRef(name=str(inner), kind="unresolved")
        return TypeRef(name="list", kind="container", args=[inner])

    def attr_arg(self, items):
        if len(items) == 2:
            return ("kw", (str(items[0]), items[1]))
        else:
            return ("pos", items[0])

    def attr_args(self, items):
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        for kind, payload in items:
            if kind == "pos":
                args.append(payload)
            else:
                key, val = payload
                kwargs[str(key)] = val
        return {"args": args, "kwargs": kwargs}

    def decorator(self, items):
        name = str(items[0])
        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        if len(items) > 1 and isinstance(items[1], dict):
            args = items[1]["args"]
            kwargs = items[1]["kwargs"]
        return Decorator(name=name, args=args, kwargs=kwargs)

    def attr_kv(self, items):
        key = str(items[0])
        val = items[1]
        return Attribute(name=key, args=[val], kwargs={}, inline=True)

    def attr_inline(self, items):
        return list(items)

    def field(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        typ = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        if not isinstance(typ, TypeRef):
            typ = TypeRef(name=str(typ), kind="unresolved")
        return ModelField(
            name=name,
            type=typ,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
        )

    def return_field(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        typ = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        if not isinstance(typ, TypeRef):
            typ = TypeRef(name=str(typ), kind="unresolved")
        return ReturnField(
            name=name,
            type=typ,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
        )

    def return_struct(self, items):
        fields = [f for f in items if isinstance(f, ReturnField)]
        return InlineStruct(fields=fields)

    def return_type(self, items):
        val = items[0]
        if isinstance(val, InlineStruct):
            return val
        if isinstance(val, TypeRef):
            return val
        return TypeRef(name=str(val), kind="unresolved")

    def model_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        is_domain = False
        if idx < len(items) and items[idx] == "domain":
            is_domain = True
            idx += 1
        name = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        fields = [f for f in items[idx:] if isinstance(f, ModelField)]
        return Model(
            name=name,
            fields=fields,
            attrs=inline_attrs,
            domain=is_domain,
            decorators=decorators or None,
            doc=doc_text,
        )

    def enum_member(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = str(items[idx])
        idx += 1
        value: int | str | None = None
        # Skip '=' if grammar passed it through
        if idx < len(items) and isinstance(items[idx], str) and items[idx] == "=":
            idx += 1
        # Accept optional literal (STRING or NUMBER) provided by grammar
        if idx < len(items) and not isinstance(items[idx], list):
            lit = items[idx]
            if isinstance(lit, (int, float)):
                value = int(lit)
                idx += 1
            elif isinstance(lit, str):
                value = lit
                idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        return EnumMember(
            name=name,
            value=value,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
        )

    def enum_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        is_domain = False
        if idx < len(items) and items[idx] == "domain":
            is_domain = True
            idx += 1
        # 'enum' keyword consumed by grammar; next is name
        name = str(items[idx])
        idx += 1
        base_type = "string"
        # optional ':' base handled by grammar: arrives either as builtin TypeRef or plain string token
        if idx < len(items):
            t = items[idx]
            if isinstance(t, TypeRef):
                if t.kind == "builtin" and t.name in {"string", "int"}:
                    base_type = t.name
                    idx += 1
            elif isinstance(t, str) and t in {"string", "int"}:
                base_type = t
                idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        members: list[EnumMember] = [
            m for m in items[idx:] if isinstance(m, EnumMember)
        ]
        return EnumDecl(
            name=name,
            base=base_type,
            members=members,
            attrs=inline_attrs,
            domain=is_domain,
            decorators=decorators or None,
            doc=doc_text,
        )

    def param(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        typ = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        if not isinstance(typ, TypeRef):
            typ = TypeRef(name=str(typ), kind="unresolved")
        return Param(
            name=name,
            type=typ,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
        )

    def param_list(self, items):
        return list(items)

    def rpc_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        params: list[Param] = []
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and (len(items[idx]) == 0 or isinstance(items[idx][0], Param))
        ):
            params = items[idx]
            idx += 1
        returns = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        return Rpc(
            name=name,
            params=params,
            returns=returns,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
        )

    def emit_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        params: list[Param] = []
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and (len(items[idx]) == 0 or isinstance(items[idx][0], Param))
        ):
            params = items[idx]
            idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        return Event(
            name=name,
            params=params,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
            role="emit",
        )

    def listen_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        params: list[Param] = []
        if (
            idx < len(items)
            and isinstance(items[idx], list)
            and (len(items[idx]) == 0 or isinstance(items[idx][0], Param))
        ):
            params = items[idx]
            idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        return Event(
            name=name,
            params=params,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
            role="listen",
        )

    def namespace_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        ns_items = [i for i in items[idx:] if isinstance(i, (Rpc, Event, Namespace))]
        return Namespace(
            name=name,
            items=ns_items,
            attrs=inline_attrs,
            decorators=decorators or None,
            doc=doc_text,
        )

    def service_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            inline_attrs = items[idx]
            idx += 1
        rpcs = [i for i in items[idx:] if isinstance(i, Rpc)]
        _events = [i for i in items[idx:] if isinstance(i, Event)]
        emits = [e for e in _events if getattr(e, "role", None) == "emit"]
        listens = [e for e in _events if getattr(e, "role", None) == "listen"]
        namespaces = [i for i in items[idx:] if isinstance(i, Namespace)]
        return Service(
            name=name,
            rpcs=rpcs,
            emits=emits,
            listens=listens,
            attrs=inline_attrs,
            decorators=decorators or None,
            namespaces=namespaces or None,
            doc=doc_text,
        )

    def service_item(self, items):
        return items[0]

    def error_decl(self, items):
        idx = 0
        doc_text: str | None = None
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "__doc__"
        ):
            doc_text = str(items[idx][1])
            idx += 1
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        is_domain = False
        if idx < len(items) and items[idx] == "domain":
            is_domain = True
            idx += 1
        name = items[idx]
        idx += 1
        inline_attrs: list[Attribute] = []
        if idx < len(items) and isinstance(items[idx], list):
            # inline [attrs] are parsed into a list
            inline_attrs = items[idx]
            idx += 1
        # Remaining items are ModelField entries (due to reuse of `field` grammar) → convert to Param
        model_fields: list[ModelField] = [
            it for it in items[idx:] if isinstance(it, ModelField)
        ]
        params: list[Param] = []
        for f in model_fields:
            params.append(
                Param(
                    name=f.name,
                    type=f.type,
                    attrs=f.attrs,
                    decorators=f.decorators,
                    doc=f.doc,
                )
            )
        return ErrorDecl(
            name=name,
            params=params,
            attrs=inline_attrs,
            domain=is_domain,
            decorators=decorators or None,
            doc=doc_text,
        )

    def decl(self, items):
        return items[0]

    def import_model(self, items):
        name = str(items[0])
        alias = str(items[1]) if len(items) > 1 else None
        return ImportItem(kind="model", name=name, alias=alias)

    def import_error(self, items):
        name = str(items[0])
        alias = str(items[1]) if len(items) > 1 else None
        return ImportItem(kind="error", name=name, alias=alias)

    def import_service(self, items):
        name = str(items[0])
        alias = str(items[1]) if len(items) > 1 else None
        return ImportItem(kind="service", name=name, alias=alias)

    def import_enum(self, items):
        name = str(items[0])
        alias = str(items[1]) if len(items) > 1 else None
        return ImportItem(kind="enum", name=name, alias=alias)

    def import_stmt(self, items):
        module = str(items[0])
        items_list = [i for i in items[1:] if isinstance(i, ImportItem)]
        return ImportStmt(module=module, items=items_list)

    def service_link(self, items):
        name = str(items[0])
        module = str(items[1])
        return ServiceLink(name=name, module=module)

    def services_block(self, items):
        vals: list[Any] = []
        for i in items:
            if isinstance(i, ServiceLink) or isinstance(i, str):
                vals.append(i)
        return vals

    def service_localref(self, items):
        return str(items[0])

    def service_item_infra(self, items):
        return items[0]

    def infrastructure_file(self, items):
        infra: Infrastructure | None = None
        decls: list[Any] = []
        imports: list[ImportStmt] = []
        for it in items:
            if isinstance(it, Infrastructure):
                infra = it
            elif isinstance(it, (Model, ErrorDecl, Service, EnumDecl)):
                decls.append(it)
            elif isinstance(it, ImportStmt):
                imports.append(it)
        if infra is None:
            raise AmiParseError(
                "infrastructure is required in infrastructure_file", stage="parse"
            )
        return InfrastructureFile(infrastructure=infra, decls=decls, imports=imports)

    def infrastructure(self, items):
        idx = 0
        decorators: list[Decorator] = []
        while idx < len(items) and isinstance(items[idx], Decorator):
            decorators.append(items[idx])
            idx += 1
        name = str(items[idx])
        idx += 1
        services: list[ServiceLink] = []
        refs: list[str] = []
        acl_rules: list[AclRule] | None = None
        for it in items[idx:]:
            if isinstance(it, list):
                if not it:
                    continue
                if isinstance(it[0], AclRule):
                    if acl_rules is None:
                        acl_rules = []
                    acl_rules.extend(it)  # type: ignore[arg-type]
                else:
                    for x in it:
                        if isinstance(x, ServiceLink):
                            services.append(x)
                        elif isinstance(x, str):
                            refs.append(x)
            elif isinstance(it, AclRule):
                if acl_rules is None:
                    acl_rules = []
                acl_rules.append(it)
        return Infrastructure(
            name=name,
            services=services,
            refs=refs,
            attrs=None,
            decorators=decorators or None,
            acl=acl_rules,
        )

    def module_file(self, items):
        module_name: str | None = None
        imports: list[ImportStmt] = []
        decls: list[Any] = []
        for i in items:
            if isinstance(i, ImportStmt):
                imports.append(i)
            elif isinstance(i, (Model, ErrorDecl, Service, EnumDecl)):
                decls.append(i)
            elif isinstance(i, str):
                module_name = i
        return ModuleFile(imports=imports, decls=decls, module=module_name)

    def module_decl(self, items):
        return str(items[0])

    def acl_block(self, items):
        return [it for it in items if isinstance(it, AclRule)]

    def acl_rule(self, items):
        subject = str(items[0])
        actions: list[AclAction] = []

        def _flatten(obj: Any) -> None:
            if isinstance(obj, AclAction):
                actions.append(obj)
            elif isinstance(obj, list):
                for x in obj:
                    _flatten(x)

        for it in items[1:]:
            _flatten(it)
        return AclRule(subject=subject, actions=actions)

    def call_action(self, items):
        target = str(items[0])
        return AclAction(kind="call", target=target)

    def listen_action(self, items):
        target = str(items[0])
        return AclAction(kind="listen", target=target)

    def acl_action(self, items):
        return items[0] if items else None


def parse_text(text: str, *, file: str | Path | None = None) -> Spec:
    parser = _load_parser()
    try:
        tree = parser.parse(text)
        ast = ToAst().transform(tree)
        return ast
    except AmiParseError:
        raise
    except UnexpectedInput as ex:
        raise AmiParseError(
            ex.__class__.__name__ + ": " + str(ex),
            file=file,
            line=getattr(ex, "line", None),
            column=getattr(ex, "column", None),
            stage="parse",
            hint="Check the syntax near the indicated position",
            cause=ex,
        )
    except Exception as ex:
        raise AmiParseError(
            str(ex),
            file=file,
            stage="parse",
            cause=ex,
        )


def parse_file(path: str | Path) -> Spec:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as ex:
        raise AmiParseError(f"Failed to read file: {p}", file=p, stage="read", cause=ex)
    return parse_text(text, file=p)

from dataclasses import dataclass
from typing import Any


@dataclass
class Attribute:
    name: str
    args: list[Any]
    kwargs: dict[str, Any]
    inline: bool


@dataclass
class Decorator:
    name: str
    args: list[Any]
    kwargs: dict[str, Any]


@dataclass
class ModelField:
    name: str
    type: "TypeRef"
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class EnumMember:
    name: str
    value: int | str | None
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class EnumDecl:
    name: str
    base: str  # "string" | "int"
    members: list[EnumMember]
    attrs: list[Attribute]
    domain: bool = False
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class Model:
    name: str
    fields: list[ModelField]
    attrs: list[Attribute]
    domain: bool = False
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class Param:
    name: str
    type: "TypeRef"
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class Rpc:
    name: str
    params: list[Param]
    returns: "TypeRef | InlineStruct"
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class Event:
    name: str
    params: list[Param]
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None
    # "emit" or "listen"
    role: str | None = None


@dataclass
class Namespace:
    name: str
    items: list[Any]
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class Service:
    name: str
    rpcs: list[Rpc]
    emits: list[Event]
    listens: list[Event]
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    namespaces: list[Namespace] | None = None
    doc: str | None = None


@dataclass
class ErrorDecl:
    name: str
    params: list[Param]
    attrs: list[Attribute]
    domain: bool = False
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class Spec:
    subject: "Subject"
    decls: list[Any]
    errors: list[ErrorDecl] | None = None


@dataclass
class ReturnField:
    name: str
    type: "TypeRef"
    attrs: list[Attribute]
    decorators: list[Decorator] | None = None
    doc: str | None = None


@dataclass
class InlineStruct:
    fields: list[ReturnField]


@dataclass(frozen=True)
class TypeRef:
    name: str
    kind: str  # "unresolved" | "builtin" | "well_known" | "model" | "error" | "enum" | "container"
    namespace: str | None = None
    absolute_id: str | None = None  # e.g. "hello.services.greeter:User"
    is_domain: bool = False
    # Optional generic arguments; for list[T] → name="list", kind="container", args=[T]
    args: list["TypeRef"] | None = None
    # Optional marker (e.g., bool? or User?)
    optional: bool = False

    def __hash__(self) -> int:  # make hash stable even if args is a list
        args_tuple = None
        if self.args is not None:
            # Convert to tuple to ensure hashability; elements are TypeRef which are also hashable
            args_tuple = tuple(self.args)
        return hash(
            (
                self.name,
                self.kind,
                self.namespace,
                self.absolute_id,
                self.is_domain,
                args_tuple,
                self.optional,
            )
        )


# AST for files
@dataclass
class ImportItem:
    kind: str  # "model" | "error" | "service"
    name: str
    alias: str | None


@dataclass
class ImportStmt:
    module: str  # file path string as in grammar (may start with $/)
    items: list[ImportItem]


@dataclass
class ServiceLink:
    name: str
    module: str


@dataclass
class AclAction:
    kind: str  # "call" | "listen"
    target: str  # dotted name


@dataclass
class AclRule:
    subject: str  # service name
    actions: list[AclAction]


@dataclass
class Infrastructure:
    name: str
    services: list[ServiceLink]
    refs: list[str]
    attrs: list[Attribute] | None = None
    decorators: list[Decorator] | None = None
    acl: list[AclRule] | None = None


@dataclass
class InfrastructureFile:
    infrastructure: Infrastructure
    decls: list[Any]
    imports: list[ImportStmt]


@dataclass
class ModuleFile:
    imports: list[ImportStmt]
    decls: list[Any]
    module: str | None = None


@dataclass
class Subject:
    name: str

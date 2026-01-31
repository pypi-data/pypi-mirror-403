from dataclasses import dataclass
from pathlib import Path

from amic.ast.model import (
    AclRule,
    EnumDecl,
    ErrorDecl,
    Model,
    ModuleFile,
    Service,
    Spec,
)


@dataclass
class ModuleUnit:
    ns: str
    path: Path
    ast: ModuleFile


@dataclass
class CompiledService:
    name: str
    module: str
    service: Service
    local_models: list[Model]
    local_errors: list[ErrorDecl]
    dep_error_modules: dict[str, list[ErrorDecl]]
    rpc_error_modules: dict[str, list[str]]
    imported_model_modules: dict[str, str]
    domain_models: list[Model] | None = None
    domain_errors: list[ErrorDecl] | None = None
    non_domain_models: list[Model] | None = None
    non_domain_errors: list[ErrorDecl] | None = None
    # Enums (optional, for future use if we decide to generate local enums)
    local_enums: list[EnumDecl] | None = None


@dataclass
class CompiledProject:
    spec: Spec
    subject_prefix: str
    services: list[CompiledService]
    domain_models: list[Model]
    domain_errors: list[ErrorDecl]
    domain_enums: list[EnumDecl]
    acl: list[AclRule] | None = None


# Well-known virtual module namespace
WELL_KNOWN_NAMESPACE = "__WELL_KNOWN__"

# Registry of available well-known types for validation
WELL_KNOWN_TYPES = {"UUID", "Datetime", "Date", "Time", "Decimal"}

# Registry of available well-known errors for validation
WELL_KNOWN_ERRORS = {
    # 4xx Client Errors
    "BadRequest",
    "InvalidArgument",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "ValidationError",
    "RateLimited",
    # 5xx Server Errors
    "InternalError",
    "ServiceUnavailable",
}

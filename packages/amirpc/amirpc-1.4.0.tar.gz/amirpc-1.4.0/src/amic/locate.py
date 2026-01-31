from functools import lru_cache
from pathlib import Path

from amic.ast.model import (
    EnumDecl,
    ErrorDecl,
    Event,
    Infrastructure,
    Model,
    Rpc,
    Service,
)


@lru_cache(maxsize=128)
def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_line(path: Path, substring: str) -> int | None:
    try:
        text = _read_text(path)
    except Exception:
        return None
    lowered = text.splitlines()
    lowered = [s.lower() for s in lowered]
    sub = substring.lower()
    for i, line in enumerate(lowered, start=1):
        if sub in line:
            return i
    return None


def _find_first_line(path: Path, patterns: list[str]) -> int | None:
    try:
        text = _read_text(path)
    except Exception:
        return None
    lines = text.splitlines()
    lowered = [s.lower() for s in lines]
    for p in patterns:
        pl = p.lower()
        for i, line in enumerate(lowered, start=1):
            if pl in line:
                return i
    return None


def loc_module_decl_line(path: Path) -> int | None:
    return _find_first_line(path, ['module "', "module '"])


def loc_service_line(path: Path, service_name: str) -> int | None:
    return _find_first_line(path, [f"service {service_name}"])


def loc_rpc_line(path: Path, rpc_name: str) -> int | None:
    return _find_first_line(path, [f"rpc {rpc_name}("])


def loc_model_line(path: Path, model_name: str) -> int | None:
    return _find_first_line(
        path,
        [
            f"model {model_name} ",
            f"model {model_name}[",
            f"model {model_name}\t",
            f"model {model_name}\n",
        ],
    )


def loc_enum_line(path: Path, enum_name: str) -> int | None:
    return _find_first_line(
        path,
        [
            f"enum {enum_name} ",
            f"enum {enum_name}[",
            f"enum {enum_name}:",
            f"enum {enum_name}\t",
            f"enum {enum_name}\n",
        ],
    )


def loc_error_line(path: Path, error_name: str) -> int | None:
    return _find_first_line(path, [f"error {error_name}("])


def loc_ref_line(path: Path, ref: str) -> int | None:
    return _find_first_line(path, [f'"{ref}"', f"'{ref}'", ref])


def loc_type_usage_line(path: Path, type_name: str) -> int | None:
    return _find_first_line(
        path, [f": {type_name}", f"-> {type_name}", f" {type_name} "]
    )


def loc_event_line(path: Path, event_name: str) -> int | None:
    return _find_first_line(path, [f"event {event_name}("])


def loc_infrastructure_line(path: Path, infra_name: str) -> int | None:
    return _find_first_line(path, [f"infrastructure {infra_name}"])


def loc_name_colon_line(path: Path, name: str) -> int | None:
    return _find_first_line(
        path, [f" {name}:", f"\n{name}:", f"\t{name}:", f" {name} :"]
    ) or _find_first_line(path, [f"{name}: "])


def locate_header_line(p: Path, node: object) -> int | None:
    name = getattr(node, "name", "")
    if isinstance(node, Infrastructure):
        return loc_infrastructure_line(p, name)
    if isinstance(node, Service):
        return loc_service_line(p, name)
    if isinstance(node, Rpc):
        return loc_rpc_line(p, name)
    if isinstance(node, Event):
        return loc_event_line(p, name)
    if isinstance(node, ErrorDecl):
        return loc_error_line(p, name)
    if isinstance(node, EnumDecl):
        return loc_enum_line(p, name)
    if isinstance(node, Model):
        return loc_model_line(p, name)
    return loc_name_colon_line(p, name)

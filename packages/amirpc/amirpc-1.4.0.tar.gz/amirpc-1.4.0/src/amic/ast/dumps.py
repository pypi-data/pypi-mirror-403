from dataclasses import asdict
from typing import Any


def to_jsonable(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_jsonable(i) for i in obj]
    return obj


def dump_ast(obj: Any, *, indent: int = 2) -> str:
    def _is_dataclass_instance(o: Any) -> bool:
        return hasattr(o, "__dataclass_fields__")

    def _dump(o: Any, level: int) -> str:
        pad = " " * (indent * level)
        next_pad = " " * (indent * (level + 1))

        if _is_dataclass_instance(o):
            cls_name = o.__class__.__name__
            field_names = list(o.__dataclass_fields__.keys())
            if not field_names:
                return f"{cls_name}()"
            parts: list[str] = []
            for name in field_names:
                value = getattr(o, name)
                dumped = _dump(value, level + 1)
                parts.append(f"{next_pad}{name}={dumped},")
            body = "\n".join(parts)
            return f"{cls_name}(\n{body}\n{pad})"

        if isinstance(o, list):
            if not o:
                return "[]"
            items = [f"{next_pad}{_dump(i, level + 1)}," for i in o]
            return "[\n" + "\n".join(items) + f"\n{pad}]"

        if isinstance(o, str):
            return repr(o)

        return repr(o)

    return _dump(obj, 0)

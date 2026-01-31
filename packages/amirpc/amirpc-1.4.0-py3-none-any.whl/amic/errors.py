from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class AmiErrorLocation:
    file: Path | None = None
    line: int | None = None
    column: int | None = None


class AmiToolError(Exception):
    """Base AMI error with extra context (file/position/hints)."""

    def __init__(
        self,
        message: str,
        *,
        file: str | Path | None = None,
        line: int | None = None,
        column: int | None = None,
        stage: str | None = None,
        hint: str | None = None,
        notes: Iterable[str] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.location = AmiErrorLocation(Path(file) if file else None, line, column)
        self.stage: str | None = stage
        self.hint: str | None = hint
        self.notes: list[str] = list(notes or [])
        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "stage": self.stage,
            "location": asdict(self.location),
            "hint": self.hint,
            "notes": list(self.notes),
        }


class AmiToolParseError(AmiToolError):
    pass


class AmiToolCompileError(AmiToolError):
    pass


class AmiToolValidationError(AmiToolError):
    pass

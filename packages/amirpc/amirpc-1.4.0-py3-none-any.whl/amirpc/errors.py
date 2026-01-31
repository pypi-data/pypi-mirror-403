from typing import Any, ClassVar

from pydantic import BaseModel

from .types import AmiErrorEnvelope


class AmiServiceError(Exception):
    """Base class for service-level AMI errors with typed data payloads."""

    code: ClassVar[str] = "error"
    default_message: ClassVar[str | None] = None
    data_model: ClassVar[type[BaseModel] | None] = None

    def __init__(
        self,
        message: str | None = None,
        *,
        code_override: str | None = None,
        **data: Any,
    ) -> None:
        self._code = code_override or type(self).code
        self.message = message or type(self).default_message or self._code
        self._data_model_instance: BaseModel | None = None
        self._raw_data: dict[str, Any] | None = None
        if type(self).data_model is not None:
            self._data_model_instance = type(self).data_model(**data)  # type: ignore[call-arg]
        else:
            self._raw_data = data or None
        super().__init__(self.message)

    def to_envelope(self) -> AmiErrorEnvelope:
        if self._data_model_instance is not None:
            data = self._data_model_instance.model_dump()
        else:
            data = self._raw_data
        return AmiErrorEnvelope(code=self._code, message=self.message, data=data)

    def __str__(self) -> str:  # pragma: no cover
        return self.message


class ServiceUnavailableError(AmiServiceError):
    code: ClassVar[str] = "service_unavailable"
    default_message: ClassVar[str | None] = "Service unavailable or response timeout"
    http_status: ClassVar[int] = 503


class UnspecifiedError(AmiServiceError):
    code: ClassVar[str] = "unspecified"
    default_message: ClassVar[str | None] = "Unspecified transport/request error"
    http_status: ClassVar[int] = 500


class UnknownRemoteError(AmiServiceError):
    code: ClassVar[str] = "unknown_remote_error"
    default_message: ClassVar[str | None] = "Unknown remote error"
    http_status: ClassVar[int] = 500


# ========================================
# Well-known HTTP Errors (4xx Client Errors)
# ========================================


class BadRequestError(AmiServiceError):
    """HTTP 400 - Invalid or malformed request."""

    code: ClassVar[str] = "bad_request"
    default_message: ClassVar[str | None] = "Invalid or malformed request"
    http_status: ClassVar[int] = 400


class UnauthorizedError(AmiServiceError):
    """HTTP 401 - Authentication required."""

    code: ClassVar[str] = "unauthorized"
    default_message: ClassVar[str | None] = "Authentication required"
    http_status: ClassVar[int] = 401


class ForbiddenError(AmiServiceError):
    """HTTP 403 - Access denied."""

    code: ClassVar[str] = "forbidden"
    default_message: ClassVar[str | None] = "Access denied"
    http_status: ClassVar[int] = 403


class NotFoundError(AmiServiceError):
    """HTTP 404 - Resource not found."""

    code: ClassVar[str] = "not_found"
    default_message: ClassVar[str | None] = "Resource not found"
    http_status: ClassVar[int] = 404


class ConflictError(AmiServiceError):
    """HTTP 409 - Resource conflict."""

    code: ClassVar[str] = "conflict"
    default_message: ClassVar[str | None] = "Resource conflict"
    http_status: ClassVar[int] = 409


class ValidationError(AmiServiceError):
    """HTTP 422 - Validation failed."""

    code: ClassVar[str] = "validation_error"
    default_message: ClassVar[str | None] = "Validation failed"
    http_status: ClassVar[int] = 422


class RateLimitedError(AmiServiceError):
    """HTTP 429 - Too many requests."""

    code: ClassVar[str] = "rate_limited"
    default_message: ClassVar[str | None] = "Too many requests"
    http_status: ClassVar[int] = 429


# ========================================
# Well-known HTTP Errors (5xx Server Errors)
# ========================================


class InternalError(AmiServiceError):
    """HTTP 500 - Internal server error."""

    code: ClassVar[str] = "internal_error"
    default_message: ClassVar[str | None] = "Internal server error"
    http_status: ClassVar[int] = 500


# ServiceUnavailableError already defined above (HTTP 503)


# ========================================
# Errors Registry
# ========================================

ERRORS: dict[str, type[AmiServiceError]] = {
    "bad_request": BadRequestError,
    "unauthorized": UnauthorizedError,
    "forbidden": ForbiddenError,
    "not_found": NotFoundError,
    "conflict": ConflictError,
    "validation_error": ValidationError,
    "rate_limited": RateLimitedError,
    "internal_error": InternalError,
    "service_unavailable": ServiceUnavailableError,
    "unspecified": UnspecifiedError,
    "unknown_remote_error": UnknownRemoteError,
}

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AmiModel(BaseModel):
    """Base marker class for all AMI models."""

    class Config:
        from_attributes = True


class AmiRequestPayload(AmiModel):
    """Base marker class for request payloads."""


class AmiResponsePayload(AmiModel):
    """Base marker class for response payloads."""


class AmiEventPayload(AmiModel):
    """Base marker class for event payloads."""


class AmiErrorEnvelope(AmiModel):
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: dict[str, Any] | None = Field(default=None, description="Additional data")


class AmiRequest[T: AmiRequestPayload](BaseModel):
    """Generic NATS request wrapper."""

    version: int = Field(default=1, description="Envelope version for schema evolution")
    request_id: UUID = Field(
        default_factory=uuid4, description="Unique request ID for correlation"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Request timestamp",
    )
    payload: T = Field(..., description="Request data")


class AmiResponse[T](BaseModel):
    """Generic NATS response wrapper.

    T may be an AmiModel or a primitive JSON type (str, int, float, bool, None, dict, list).
    """

    version: int = Field(default=1, description="Envelope version for schema evolution")
    request_id: UUID | None = Field(
        default=None, description="Request ID for correlation"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response timestamp",
    )
    payload: T | None = Field(default=None, description="Response data")
    error: AmiErrorEnvelope | None = Field(default=None, description="Error")


class AmiEvent[T: AmiEventPayload](BaseModel):
    """Generic NATS event wrapper."""

    version: int = Field(default=1, description="Envelope version for schema evolution")
    id: UUID = Field(..., description="Event ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Event timestamp",
    )
    source: str | None = Field(default=None, description="Source service")
    payload: T = Field(..., description="Event data")


class HealthStatus(AmiModel):
    """Universal health check response for all AMI services."""

    alive: bool = Field(default=True, description="Service is alive and responding")
    ready: bool = Field(default=True, description="Service is ready to accept requests")
    service: str = Field(..., description="Service name")
    version: str | None = Field(default=None, description="Service version")
    hostname: str = Field(..., description="Host where service is running")
    server: str | None = Field(default=None, description="Server identifier")
    instance_id: str | None = Field(default=None, description="Instance identifier")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


__all__ = [
    "AmiErrorEnvelope",
    "AmiEvent",
    "AmiEventPayload",
    "AmiModel",
    "AmiRequest",
    "AmiRequestPayload",
    "AmiResponse",
    "AmiResponsePayload",
    "HealthStatus",
]

"""Runtime configuration for amirpc."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    """Configuration for NATS runtime connection.

    Attributes:
        nats_url: NATS server URL (default: nats://localhost:4222)
        creds_file: Path to .creds file for authentication (optional)
        service_version: Version string for service identification (optional)
        service_server: Server/host identifier for health checks (optional)
        service_instance_id: Unique instance ID for health checks (optional)
        connect_timeout: Connection timeout in seconds (default: 2.0)
        reconnect_time_wait: Time to wait between reconnection attempts (default: 2.0)
        max_reconnect_attempts: Maximum number of reconnection attempts (default: 60)
        expand_srv: Resolve DNS SRV records and expand to multiple server URLs (default: True)
        drain_timeout: Timeout in seconds for draining NATS connection on shutdown (default: 25.0)
    """

    nats_url: str = "nats://localhost:4222"
    creds_file: str | None = None
    service_version: str | None = None
    service_server: str | None = None
    service_instance_id: str | None = None
    connect_timeout: float = 2.0
    reconnect_time_wait: float = 2.0
    max_reconnect_attempts: int = 60
    expand_srv: bool = True
    drain_timeout: float = 25.0

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        """Create RuntimeConfig from environment variables.

        Environment variables:
            NATS_URL: NATS server URL (default: nats://localhost:4222)
            NATS_CREDS_FILE: Path to .creds file (optional)
            AMI_SERVICE_VERSION: Service version string (optional)
            AMI_SERVICE_SERVER: Server/host identifier (optional)
            AMI_SERVICE_INSTANCE_ID: Unique instance ID (optional)
        """
        return cls(
            nats_url=os.environ.get("NATS_URL", "nats://localhost:4222"),
            creds_file=os.environ.get("NATS_CREDS_FILE"),
            service_version=os.environ.get("AMI_SERVICE_VERSION"),
            service_server=os.environ.get("AMI_SERVICE_SERVER"),
            service_instance_id=os.environ.get("AMI_SERVICE_INSTANCE_ID"),
        )


__all__ = ["RuntimeConfig"]

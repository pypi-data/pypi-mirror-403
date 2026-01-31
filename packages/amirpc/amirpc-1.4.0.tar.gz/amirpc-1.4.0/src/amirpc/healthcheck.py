#!/usr/bin/env python3
"""
Health check script for Kubernetes/Docker probes.

Usage:
    python -m amirpc.healthcheck [options]

Environment variables (follows AMI platform conventions):
    AMI_NATS_URL              - NATS server URL (default: nats://localhost:4222)
    AMI_NATS_TIMEOUT          - NATS request timeout in seconds (default: 5)
    AMI_NATS_CREDENTIALS_FILE - Path to NATS credentials file for auth (optional)
    AMI_SERVICE_NAME          - Service name to check (e.g., orchestrator)
    AMI_SUBJECT_PREFIX        - Subject prefix (default: ami)

Exit codes:
    0 - Service is alive and ready
    1 - Service is alive but not ready
    2 - Service is not alive or unreachable
    3 - Configuration error

Examples:
    # Check orchestrator service
    AMI_SERVICE_NAME=orchestrator amirpc-health

    # With custom NATS URL
    AMI_NATS_URL=nats://nats:4222 AMI_SERVICE_NAME=worker amirpc-health

    # Check only liveness (ignore ready status)
    AMI_SERVICE_NAME=orchestrator amirpc-health --liveness-only

    # Using CLI arguments
    amirpc-health --service orchestrator --nats-url nats://nats:4222
"""

import argparse
import asyncio
import os
import sys
from logging import getLogger

logger = getLogger(__name__)
getLogger("asyncio").setLevel("ERROR")


async def check_health(
    nats_url: str,
    service_name: str,
    subject_prefix: str = "ami",
    timeout: float = 5.0,
    liveness_only: bool = False,
    credentials_file: str | None = None,
) -> tuple[int, str]:
    """
    Check health of a service via NATS.

    Returns:
        Tuple of (exit_code, message)
    """
    import nats
    from nats.errors import NoRespondersError, TimeoutError

    from amirpc.types import AmiResponse, HealthStatus

    subject = f"{subject_prefix}.{service_name}._internal.rpc.health"

    try:
        connect_kwargs: dict = {"servers": [nats_url]}
        if credentials_file:
            connect_kwargs["user_credentials"] = credentials_file

        nc = await nats.connect(**connect_kwargs)

        try:
            response = await nc.request(
                subject=subject,
                payload=b"{}",
                timeout=timeout,
            )
            resp = AmiResponse[HealthStatus].model_validate_json(response.data)

            if resp.error is not None:
                return 2, f"Health check error: {resp.error.message}"

            if resp.payload is None:
                return 2, "Empty health response"

            status = resp.payload

            if not status.alive:
                return 2, f"Service {service_name} is not alive"

            if not liveness_only and not status.ready:
                return 1, f"Service {service_name} is alive but not ready"

            info = f"alive={status.alive} ready={status.ready}"
            if status.version:
                info += f" version={status.version}"
            info += f" uptime={status.uptime_seconds:.1f}s"
            info += f" host={status.hostname}"

            return 0, f"Service {service_name} is healthy: {info}"

        finally:
            await nc.close()

    except TimeoutError:
        return 2, f"Health check timeout: service {service_name} not responding"
    except NoRespondersError:
        return 2, f"Health check failed: no responders for service {service_name}"
    except Exception as e:
        return 2, f"Health check failed: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Health check for AMI services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--service",
        "-s",
        default=os.environ.get("AMI_SERVICE_NAME"),
        help="Service name to check (or set AMI_SERVICE_NAME env var)",
    )
    parser.add_argument(
        "--nats-url",
        "-n",
        default=os.environ.get("AMI_NATS_URL"),
        help="NATS server URL",
    )
    parser.add_argument(
        "--prefix",
        "-p",
        default=os.environ.get("AMI_SUBJECT_PREFIX", "ami"),
        help="Subject prefix (default: ami)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=float(os.environ.get("AMI_NATS_TIMEOUT", "5")),
        help="Timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--credentials",
        "-c",
        default=os.environ.get("AMI_NATS_CREDENTIALS_FILE"),
        help="Path to NATS credentials file (or set AMI_NATS_CREDENTIALS_FILE)",
    )
    parser.add_argument(
        "--liveness-only",
        "-l",
        action="store_true",
        help="Only check liveness, ignore ready status",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output, only return exit code",
    )

    args = parser.parse_args()

    if not args.service:
        if not args.quiet:
            print(
                "Error: AMI_SERVICE_NAME not set and --service not provided",
                file=sys.stderr,
            )
        return 3

    if not args.nats_url:
        if not args.quiet:
            print(
                "Error: AMI_NATS_URL not set and --nats-url not provided",
                file=sys.stderr,
            )
        return 3

    exit_code, message = asyncio.run(
        check_health(
            nats_url=args.nats_url,
            service_name=args.service,
            subject_prefix=args.prefix,
            timeout=args.timeout,
            liveness_only=args.liveness_only,
            credentials_file=args.credentials,
        )
    )

    if not args.quiet:
        if exit_code == 0:
            print(message)
        else:
            print(message, file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

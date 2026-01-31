"""Gateway runtime for auto-generating FastAPI routes from metadata."""

try:
    from amirpc.gateway.runtime import AutoGateway
except ImportError:
    raise ImportError(
        "FastAPI is required for gateway. Install it with: pip install amirpc[gateway]"
    ) from None

__all__ = ["AutoGateway"]

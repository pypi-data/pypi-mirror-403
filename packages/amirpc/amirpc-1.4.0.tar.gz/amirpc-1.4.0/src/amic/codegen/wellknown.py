"""Well-known types and errors mapping to Python implementation."""

from typing import Any

# Mapping of ASL well-known types to Python implementation details
WELL_KNOWN_MAPPINGS: dict[str, dict[str, Any]] = {
    "UUID": {"py_type": "UUID", "import": ("uuid", "UUID")},
    "Datetime": {"py_type": "datetime", "import": ("datetime", "datetime")},
    "Date": {"py_type": "date", "import": ("datetime", "date")},
    "Time": {"py_type": "time", "import": ("datetime", "time")},
    "Decimal": {"py_type": "Decimal", "import": ("decimal", "Decimal")},
}

# Mapping of well-known errors to Python exceptions and HTTP status codes
WELL_KNOWN_ERRORS: dict[str, dict[str, Any]] = {
    # 4xx Client Errors
    "BadRequest": {
        "py_type": "BadRequestError",
        "import": ("amirpc.errors", "BadRequestError"),
        "http_status": 400,
        "description": "Invalid or malformed request",
    },
    "Unauthorized": {
        "py_type": "UnauthorizedError",
        "import": ("amirpc.errors", "UnauthorizedError"),
        "http_status": 401,
        "description": "Authentication required",
    },
    "Forbidden": {
        "py_type": "ForbiddenError",
        "import": ("amirpc.errors", "ForbiddenError"),
        "http_status": 403,
        "description": "Access denied",
    },
    "NotFound": {
        "py_type": "NotFoundError",
        "import": ("amirpc.errors", "NotFoundError"),
        "http_status": 404,
        "description": "Resource not found",
    },
    "Conflict": {
        "py_type": "ConflictError",
        "import": ("amirpc.errors", "ConflictError"),
        "http_status": 409,
        "description": "Resource conflict",
    },
    "ValidationError": {
        "py_type": "ValidationError",
        "import": ("amirpc.errors", "ValidationError"),
        "http_status": 422,
        "description": "Validation failed",
    },
    "RateLimited": {
        "py_type": "RateLimitedError",
        "import": ("amirpc.errors", "RateLimitedError"),
        "http_status": 429,
        "description": "Too many requests",
    },
    # 5xx Server Errors
    "InternalError": {
        "py_type": "InternalError",
        "import": ("amirpc.errors", "InternalError"),
        "http_status": 500,
        "description": "Internal server error",
    },
    "ServiceUnavailable": {
        "py_type": "ServiceUnavailableError",
        "import": ("amirpc.errors", "ServiceUnavailableError"),
        "http_status": 503,
        "description": "Service temporarily unavailable",
    },
}


def get_python_type(well_known_type: str) -> str:
    """Get Python type name for a well-known ASL type."""
    mapping = WELL_KNOWN_MAPPINGS.get(well_known_type)
    if mapping:
        return mapping["py_type"]
    return well_known_type


def get_import_info(well_known_type: str) -> tuple[str, str] | None:
    """Get import information (module, name) for a well-known ASL type."""
    mapping = WELL_KNOWN_MAPPINGS.get(well_known_type)
    if mapping:
        return mapping["import"]
    return None


def is_well_known_in_codegen(typ: str) -> bool:
    """Check if a type is a well-known type from codegen perspective."""
    return typ in WELL_KNOWN_MAPPINGS


def is_well_known_error(error_name: str) -> bool:
    """Check if an error is a well-known error."""
    return error_name in WELL_KNOWN_ERRORS


def get_error_info(error_name: str) -> dict[str, Any] | None:
    """Get error information for a well-known error."""
    return WELL_KNOWN_ERRORS.get(error_name)


def get_error_http_status(error_name: str) -> int | None:
    """Get HTTP status code for a well-known error."""
    info = get_error_info(error_name)
    return info["http_status"] if info else None


def get_all_well_known_errors() -> list[str]:
    """Get list of all well-known error names."""
    return list(WELL_KNOWN_ERRORS.keys())

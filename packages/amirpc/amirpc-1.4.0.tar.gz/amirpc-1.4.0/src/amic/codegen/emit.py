"""Code emission utilities: formatting and filesystem helpers."""

import black


def format_code(code: str) -> str:
    """Format code with Black. Formatting is mandatory."""
    return black.format_str(code, mode=black.Mode())

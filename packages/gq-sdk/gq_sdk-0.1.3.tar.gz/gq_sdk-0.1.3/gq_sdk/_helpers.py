"""
Helper utilities for the gqpy SDK.

Contains utility functions for timestamps, data processing, and other
common operations used throughout the SDK.
"""

import time
from typing import Any, Dict, List, Optional


def generate_timestamp() -> int:
    """
    Return a millisecond integer timestamp.

    Returns:
        Current time in milliseconds since epoch.
    """
    return int(time.time() * 10**3)


def generate_client_algo_id() -> str:
    """
    Generate a unique client algorithm ID based on current timestamp.

    Returns:
        A string representation of the current timestamp in milliseconds.
    """
    return str(int(time.time() * 1000))


def clean_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from a dictionary.

    Args:
        data: Dictionary that may contain None values.

    Returns:
        Dictionary with None values removed.
    """
    return {k: v for k, v in data.items() if v is not None}


def format_path_params(path: str, **kwargs) -> str:
    """
    Format a path string with named parameters.

    Args:
        path: Path template with {param} placeholders.
        **kwargs: Parameter values to substitute.

    Returns:
        Formatted path string.

    Example:
        >>> format_path_params("/api/v5/account/{exchange}/{account}", exchange="okx", account="main")
        '/api/v5/account/okx/main'
    """
    return path.format(**kwargs)


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Float value or default.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Int value or default.
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

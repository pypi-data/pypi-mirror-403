"""Centralized large response handling for MCP tools.

This module provides a decorator pattern for handling large tool responses
that might exceed Claude Code's token limits. When a response exceeds a
configurable threshold (default 100KB), it:

1. Writes the full response to a JSON file
2. Returns lightweight metadata with navigation hints

This catches large responses BEFORE Claude Code's limit, providing a
controlled "success" path with better navigation guidance.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

__all__ = [
    "large_response_handler",
    "LARGE_RESPONSE_THRESHOLD_BYTES",
    "RESPONSE_DIR",
]

# Configurable threshold (default 100KB)
LARGE_RESPONSE_THRESHOLD_BYTES = int(
    os.getenv("MCP_LARGE_RESPONSE_THRESHOLD_BYTES", 100 * 1024)
)

RESPONSE_DIR = Path(tempfile.gettempdir()) / "bpa-responses"

F = TypeVar("F", bound=Callable[..., Any])


def large_response_handler(
    threshold_bytes: int | None = None,
    navigation: dict[str, str] | None = None,
) -> Callable[[F], F]:
    """Decorator that handles large responses by writing to file.

    When a tool's response exceeds the threshold, saves to a JSON file
    and returns metadata with navigation hints for AI agents.

    Args:
        threshold_bytes: Size threshold in bytes (default: 100KB).
        navigation: Dict of navigation hints (name -> jq/grep command).

    Returns:
        Decorated function that returns file_path for large responses.
    """
    effective_threshold = threshold_bytes or LARGE_RESPONSE_THRESHOLD_BYTES

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            result = await func(*args, **kwargs)

            # Measure serialized size
            json_str = json.dumps(result, default=str)
            size_bytes = len(json_str.encode("utf-8"))

            if size_bytes < effective_threshold:
                return dict(result)

            # Save to file
            file_path = _save_response_to_file(result, func.__name__)

            return {
                "file_path": str(file_path),
                "size_kb": size_bytes // 1024,
                "record_count": _count_records(result),
                "schema": _infer_schema(result),
                "navigation": navigation or _default_navigation(),
                "message": (
                    f"Large response ({size_bytes // 1024}KB) saved to file. "
                    "Use Read tool with offset/limit, Grep, or jq to query."
                ),
            }

        return wrapper  # type: ignore[return-value]

    return decorator


def _save_response_to_file(data: dict[str, Any], tool_name: str) -> Path:
    """Save response data to a temp JSON file.

    Args:
        data: The response data to save.
        tool_name: Name of the tool (used in filename).

    Returns:
        Path to the saved file.
    """
    RESPONSE_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = RESPONSE_DIR / f"{tool_name}_{timestamp}.json"

    file_path.write_text(json.dumps(data, indent=2, default=str))
    return file_path


def _infer_schema(data: dict[str, Any], max_depth: int = 2) -> dict[str, str]:
    """Infer a simple schema from the response data.

    Args:
        data: The response data to analyze.
        max_depth: Maximum depth for schema inference (unused, reserved).

    Returns:
        Dict mapping top-level keys to type descriptions.
    """
    schema: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, list):
            if value and isinstance(value[0], dict):
                schema[key] = f"[{{...}}] ({len(value)} items)"
            else:
                schema[key] = f"[...] ({len(value)} items)"
        elif isinstance(value, dict):
            schema[key] = "{...}"
        else:
            schema[key] = type(value).__name__
    return schema


def _count_records(data: dict[str, Any]) -> dict[str, int]:
    """Count array lengths in the response for quick reference.

    Args:
        data: The response data to analyze.

    Returns:
        Dict mapping array field names to their lengths.
    """
    counts: dict[str, int] = {}
    for key, value in data.items():
        if isinstance(value, list):
            counts[key] = len(value)
    return counts


def _default_navigation() -> dict[str, str]:
    """Default navigation hints for querying saved JSON files.

    Returns:
        Dict of navigation hint name -> jq command.
    """
    return {
        "view_structure": "jq 'keys'",
        "first_10_items": "jq '.[] | limit(10; .)'",
        "count_arrays": (
            'jq \'to_entries | map(select(.value | type == "array")) '
            "| from_entries | map_values(length)'"
        ),
    }

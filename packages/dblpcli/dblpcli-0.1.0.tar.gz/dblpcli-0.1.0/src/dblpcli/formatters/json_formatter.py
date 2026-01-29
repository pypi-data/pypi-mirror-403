"""JSON output formatter."""

from __future__ import annotations

import json
from typing import Any


def format_json(
    data: dict[str, Any] | list[Any],
    meta: dict[str, Any] | None = None,
    pretty: bool = True,
) -> str:
    """Format data as JSON.

    Args:
        data: The data to format (dict or list)
        meta: Optional metadata to include
        pretty: Whether to pretty-print with indentation

    Returns:
        JSON string
    """
    if isinstance(data, list):
        output = {
            "results": data,
            "meta": meta or {},
        }
    elif "results" in data or "publications" in data:
        # Already structured response
        output = data
        if meta:
            output["meta"] = {**output.get("meta", {}), **meta}
    else:
        # Single item
        output = {
            "result": data,
            "meta": meta or {},
        }

    indent = 2 if pretty else None
    return json.dumps(output, indent=indent, ensure_ascii=False)


def format_error_json(
    code: str,
    message: str,
    suggestion: str | None = None,
    **extra: Any,
) -> str:
    """Format an error as JSON.

    Args:
        code: Error code (e.g., "NOT_FOUND")
        message: Human-readable error message
        suggestion: Optional suggestion for resolution
        **extra: Additional fields to include

    Returns:
        JSON string
    """
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if suggestion:
        error["suggestion"] = suggestion
    error.update(extra)

    return json.dumps({"error": error}, indent=2, ensure_ascii=False)

"""MCP tools for BPA field operations.

This module provides tools for listing and retrieving BPA form fields.
Fields are accessed through service endpoints (service-centric API design).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)
from mcp_eregistrations_bpa.tools.large_response import large_response_handler

__all__ = ["field_list", "field_get", "register_field_tools"]


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.fields'",
        "find_by_type": "jq '.fields[] | select(.type == \"textfield\")'",
        "find_by_key": "jq '.fields[] | select(.key | contains(\"search\"))'",
        "required_only": "jq '.fields[] | select(.required == true)'",
    },
)
async def field_list(
    service_id: str | int,
    limit: int = 50,
    offset: int = 0,
    type_filter: str | None = None,
    required_only: bool = False,
) -> dict[str, Any]:
    """List fields for a service with pagination and filtering.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        service_id: The service ID to list fields for.
        limit: Maximum number of fields to return (default: 50).
        offset: Number of fields to skip (default: 0).
        type_filter: Filter by field type (e.g., "select", "textfield").
        required_only: Filter to only required fields (default: False).

    Returns:
        dict with fields, total, has_more, service_id.
    """
    # Normalize pagination parameters
    if limit <= 0:
        limit = 50
    if offset < 0:
        offset = 0

    try:
        async with BPAClient() as client:
            fields_data = await client.get_list(
                "/service/{service_id}/fields",
                path_params={"service_id": service_id},
                resource_type="field",
            )
    except BPAClientError as e:
        raise translate_error(e, resource_type="field")

    # Transform to consistent output format with snake_case keys
    all_fields = []
    for field in fields_data:
        field_obj: dict[str, Any] = {
            "key": field.get("key"),
            "name": field.get("name"),
            "type": field.get("type"),
            "required": field.get("required", False),
            "label": field.get("label"),
        }
        # Only include component_key if it has a value (remove null noise)
        if field.get("componentKey"):
            field_obj["component_key"] = field.get("componentKey")
        all_fields.append(field_obj)

    # Apply filters before sorting/pagination
    if type_filter is not None:
        all_fields = [f for f in all_fields if f.get("type") == type_filter]

    if required_only:
        all_fields = [f for f in all_fields if f.get("required") is True]

    # Sort by key for consistent pagination ordering
    all_fields.sort(key=lambda f: f.get("key") or "")

    # Calculate total before pagination
    total = len(all_fields)

    # Apply pagination
    paginated_fields = all_fields[offset : offset + limit]

    # Calculate has_more
    has_more = (offset + limit) < total

    return {
        "fields": paginated_fields,
        "total": total,
        "has_more": has_more,
        "service_id": service_id,
    }


async def field_get(service_id: str | int, field_key: str) -> dict[str, Any]:
    """Get details of a BPA field by service ID and field key.

    Args:
        service_id: The service containing the field.
        field_key: The field key/identifier within the service.

    Returns:
        dict with key, name, label, type, required, component_key, service_id.
    """
    try:
        async with BPAClient() as client:
            try:
                field_data = await client.get(
                    "/service/{service_id}/fields/{field_key}",
                    path_params={"service_id": service_id, "field_key": field_key},
                    resource_type="field",
                    resource_id=field_key,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Field '{field_key}' not found in service '{service_id}'. "
                    "Use 'field_list' with the service_id to see available fields."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="field", resource_id=field_key)

    result = {
        "key": field_data.get("key"),
        "name": field_data.get("name"),
        "label": field_data.get("label"),
        "type": field_data.get("type"),
        "required": field_data.get("required", False),
        "service_id": service_id,
    }
    # Only include component_key if it has a value (remove null noise)
    if field_data.get("componentKey"):
        result["component_key"] = field_data.get("componentKey")
    return result


def register_field_tools(mcp: Any) -> None:
    """Register field tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(field_list)
    mcp.tool()(field_get)

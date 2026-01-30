"""MCP tools for BPA external service (Mule) operations.

This module provides tools for listing and retrieving external services (GDB APIs)
available in the BPA platform. These are used by bots to connect to external data
sources.

API Endpoints used:
- GET /mule/services - List all available external services
- GET /mule/services/{service_id} - Get external service by ID (base64 encoded)
"""

from __future__ import annotations

import base64
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)
from mcp_eregistrations_bpa.tools.large_response import large_response_handler

__all__ = [
    "muleservice_list",
    "muleservice_get",
    "register_external_service_tools",
]


def _transform_muleservice_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform mule service API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "type": data.get("type"),
        "db_name": data.get("dbName"),
        "base_url": data.get("baseUrl"),
        "method": data.get("method"),
        "inputs": data.get("inputs", []),
        "outputs": data.get("outputs", []),
    }


def _transform_muleservice_list_item(data: dict[str, Any]) -> dict[str, Any]:
    """Transform mule service list item (minimal fields).

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "type": data.get("type"),
        "db_name": data.get("dbName"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,
    navigation={
        "list_all": "jq '.services'",
        "gdb_only": "jq '.services[] | select(.id | startswith(\"GDB.\"))'",
        "find_by_name": "jq '.services[] | select(.name | contains(\"search\"))'",
    },
)
async def muleservice_list(
    service_type: str | None = None,
    name_filter: str | None = None,
) -> dict[str, Any]:
    """List available external services (GDB, APIs).

    Args:
        service_type: Filter by type prefix (e.g., "GDB").
        name_filter: Filter by name substring (case-insensitive).

    Returns:
        dict with services (list of id, name, type, db_name), total.
    """
    try:
        async with BPAClient() as client:
            result = await client.get(
                "/mule/services",
                params={"withoutdata": "true"},
                resource_type="mule_service",
            )

            # Handle both list and dict responses
            if isinstance(result, list):
                services_raw = result
            else:
                services_raw = result.get("services", result.get("data", []))

            # Apply filters
            services = []
            for svc in services_raw:
                svc_id = svc.get("id", "")
                svc_name = svc.get("name", "")

                # Filter by service type prefix
                if service_type:
                    if not svc_id.upper().startswith(service_type.upper()):
                        continue

                # Filter by name substring
                if name_filter:
                    if name_filter.lower() not in svc_name.lower():
                        continue

                services.append(_transform_muleservice_list_item(svc))

            return {
                "services": services,
                "total": len(services),
                "filters_applied": {
                    "service_type": service_type,
                    "name_filter": name_filter,
                },
            }

    except BPAClientError as e:
        raise translate_error(e, resource_type="mule_service")


async def muleservice_get(service_id: str) -> dict[str, Any]:
    """Get external service details including input/output mappings.

    Args:
        service_id: Service ID (e.g., GDB.GDB-NIPC REGISTRY(2.9)-read).

    Returns:
        dict with id, name, type, db_name, base_url, inputs, outputs.
    """
    if not service_id:
        raise ToolError(
            "Cannot get mule service: 'service_id' is required. "
            "Use 'muleservice_list' to see available services."
        )

    # Service IDs need to be base64 encoded for the API
    encoded_id = base64.b64encode(service_id.encode()).decode()

    try:
        async with BPAClient() as client:
            try:
                service_data = await client.get(
                    "/mule/services/{service_id}",
                    path_params={"service_id": encoded_id},
                    resource_type="mule_service",
                    resource_id=service_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Mule service '{service_id}' not found. "
                    "Use 'muleservice_list' to see available services."
                )

        return _transform_muleservice_response(service_data)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="mule_service", resource_id=service_id)


def register_external_service_tools(mcp: Any) -> None:
    """Register external service tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(muleservice_list)
    mcp.tool()(muleservice_get)

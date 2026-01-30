"""MCP tools for BPA role unit (involved unit) operations.

Role units define organizational units assigned to workflow roles. Each role
can have one or more units that handle applications at that step.

Write operations follow the audit-before-write pattern.

API Endpoints used:
- GET /role/{role_id}/role_unit - List units assigned to role
- POST /role/{role_id}/role_unit - Assign unit to role
- GET /role_unit/{role_unit_id} - Get specific unit assignment
- DELETE /role_unit/{role_unit_id} - Remove unit from role
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.audit.context import (
    NotAuthenticatedError,
    get_current_user_email,
)
from mcp_eregistrations_bpa.audit.logger import AuditLogger
from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)
from mcp_eregistrations_bpa.tools.large_response import large_response_handler

__all__ = [
    "roleunit_list",
    "roleunit_get",
    "roleunit_create",
    "roleunit_delete",
    "register_role_unit_tools",
]


def _transform_role_unit_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform role unit API response from camelCase to snake_case.

    Based on RoleInstitution model from BPA frontend:
    - id, roleId, institutionId, unitId
    - institutionName, unitName
    - units (nested), jsonDeterminants

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "role_id": data.get("roleId"),
        "institution_id": data.get("institutionId"),
        "unit_id": data.get("unitId"),
        "institution_name": data.get("institutionName"),
        "unit_name": data.get("unitName"),
        "units": data.get("units"),
        "json_determinants": data.get("jsonDeterminants"),
        # Audit fields
        "created_by": data.get("createdBy"),
        "created_when": data.get("createdWhen"),
        "last_changed_by": data.get("lastChangedBy"),
        "last_changed_when": data.get("lastChangedWhen"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.units'",
        "by_institution": "jq '.units[] | select(.institution_id==\"x\")'",
        "by_name": "jq '.units[] | select(.unit_name | contains(\"x\"))'",
    },
)
async def roleunit_list(role_id: str | int) -> dict[str, Any]:
    """List units assigned to a role.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        role_id: Role ID to list units for.

    Returns:
        dict with units (list), role_id, total.
    """
    if not role_id:
        raise ToolError(
            "Cannot list role units: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                units_data = await client.get_list(
                    "/role/{role_id}/role_unit",
                    path_params={"role_id": role_id},
                    resource_type="role_unit",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role '{role_id}' not found. "
                    "Use 'role_list' with service_id to see available roles."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role_unit")

    units = [_transform_role_unit_response(unit) for unit in units_data]

    return {
        "units": units,
        "role_id": str(role_id),
        "total": len(units),
    }


async def roleunit_get(role_unit_id: str | int) -> dict[str, Any]:
    """Get a specific role unit assignment by ID.

    Args:
        role_unit_id: Role unit assignment ID.

    Returns:
        dict with id, role_id, unit_id, unit_name.
    """
    if not role_unit_id:
        raise ToolError(
            "Cannot get role unit: 'role_unit_id' is required. "
            "Use 'roleunit_list' with role_id to find valid IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                unit_data = await client.get(
                    "/role_unit/{role_unit_id}",
                    path_params={"role_unit_id": role_unit_id},
                    resource_type="role_unit",
                    resource_id=role_unit_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role unit '{role_unit_id}' not found. "
                    "Use 'roleunit_list' to see available assignments."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role_unit", resource_id=role_unit_id)

    return _transform_role_unit_response(unit_data)


async def roleunit_create(
    role_id: str | int,
    institution_id: str,
    unit_id: str,
    institution_name: str | None = None,
    unit_name: str | None = None,
) -> dict[str, Any]:
    """Assign a unit to a role. Audited write operation.

    Role units link organizational units (within institutions) to workflow roles.

    Args:
        role_id: Role to assign unit to.
        institution_id: Institution the unit belongs to.
        unit_id: Unit ID to assign.
        institution_name: Optional institution name for display.
        unit_name: Optional unit name for display.

    Returns:
        dict with id, role_id, institution_id, unit_id, audit_id.
    """
    # Pre-flight validation
    if not role_id:
        raise ToolError(
            "Cannot create role unit: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )
    if not institution_id:
        raise ToolError(
            "Cannot create role unit: 'institution_id' is required. "
            "Use 'roleinstitution_create' first to link an institution to the role."
        )
    if not unit_id:
        raise ToolError(
            "Cannot create role unit: 'unit_id' is required. "
            "Units are organizational departments within institutions."
        )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Build payload matching RoleInstitution model
    payload: dict[str, Any] = {
        "institutionId": institution_id,
        "unitId": unit_id,
    }
    if institution_name:
        payload["institutionName"] = institution_name
    if unit_name:
        payload["unitName"] = unit_name

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Verify role exists
            try:
                await client.get(
                    "/role/{role_id}",
                    path_params={"role_id": role_id},
                    resource_type="role",
                    resource_id=role_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role '{role_id}' not found. "
                    "Use 'role_list' with service_id to see available roles."
                )

            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="link",
                object_type="role_unit",
                params={
                    "role_id": str(role_id),
                    "institution_id": institution_id,
                    "unit_id": unit_id,
                },
            )

            try:
                result = await client.post(
                    "/role/{role_id}/role_unit",
                    path_params={"role_id": role_id},
                    json=payload,
                    resource_type="role_unit",
                )

                # Save rollback state
                created_id = result.get("id") if isinstance(result, dict) else None
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="role_unit",
                    object_id=str(created_id) if created_id else str(role_id),
                    previous_state={
                        "id": created_id,
                        "role_id": str(role_id),
                        "institution_id": institution_id,
                        "unit_id": unit_id,
                        "_operation": "create",
                    },
                )

                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "id": created_id,
                        "role_id": str(role_id),
                        "institution_id": institution_id,
                        "unit_id": unit_id,
                    },
                )

                response = (
                    _transform_role_unit_response(result)
                    if isinstance(result, dict)
                    else {
                        "id": None,
                        "role_id": str(role_id),
                        "institution_id": institution_id,
                        "unit_id": unit_id,
                    }
                )
                response["audit_id"] = audit_id
                return response

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role_unit")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


async def roleunit_delete(role_unit_id: str | int) -> dict[str, Any]:
    """Remove a unit assignment from a role. Audited write operation.

    Args:
        role_unit_id: Role unit assignment ID to delete.

    Returns:
        dict with deleted (bool), role_unit_id, deleted_unit, audit_id.
    """
    if not role_unit_id:
        raise ToolError(
            "Cannot delete role unit: 'role_unit_id' is required. "
            "Use 'roleunit_list' to find valid IDs."
        )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Capture current state for rollback
            try:
                previous_state = await client.get(
                    "/role_unit/{role_unit_id}",
                    path_params={"role_unit_id": role_unit_id},
                    resource_type="role_unit",
                    resource_id=role_unit_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role unit '{role_unit_id}' not found. "
                    "Use 'roleunit_list' to see available assignments."
                )

            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="unlink",
                object_type="role_unit",
                object_id=str(role_unit_id),
                params={},
            )

            # Save rollback state
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role_unit",
                object_id=str(role_unit_id),
                previous_state=previous_state,
            )

            try:
                await client.delete(
                    "/role_unit/{role_unit_id}",
                    path_params={"role_unit_id": role_unit_id},
                    resource_type="role_unit",
                    resource_id=role_unit_id,
                )

                await audit_logger.mark_success(
                    audit_id,
                    result={"deleted": True, "role_unit_id": str(role_unit_id)},
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="role_unit", resource_id=role_unit_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role_unit", resource_id=role_unit_id)

    return {
        "deleted": True,
        "role_unit_id": str(role_unit_id),
        "deleted_unit": _transform_role_unit_response(previous_state),
        "audit_id": audit_id,
    }


def register_role_unit_tools(mcp: Any) -> None:
    """Register role unit tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(roleunit_list)
    mcp.tool()(roleunit_get)
    mcp.tool()(roleunit_create)
    mcp.tool()(roleunit_delete)

"""MCP tools for BPA role status operations.

Role statuses define workflow transition states for roles (e.g., FILE VALIDATED,
SEND BACK). They control where applications go next in the workflow.

Write operations follow the audit-before-write pattern.

API Endpoints used:
- GET /role_status/{role_status_id} - Get role status by ID
- POST /role/{role_id}/role_status/user_defined_status - Create user-defined status
- PUT /role_status/{role_status_id}/user_defined_status - Update user-defined status
- DELETE /role_status/{role_status_id} - Delete role status
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

__all__ = [
    "rolestatus_get",
    "rolestatus_create",
    "rolestatus_update",
    "rolestatus_delete",
    "register_role_status_tools",
]


def _transform_role_status_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform role status API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "type": data.get("type"),
        "role_status_type": data.get("roleStatusType"),
        "destination_id": data.get("destinationId"),
        "role_id": data.get("roleId"),
        # Role status message (for notifications)
        "role_status_message": data.get("roleStatusMessage"),
        # Audit fields
        "created_by": data.get("createdBy"),
        "created_when": data.get("createdWhen"),
        "last_changed_by": data.get("lastChangedBy"),
        "last_changed_when": data.get("lastChangedWhen"),
    }


async def rolestatus_get(role_status_id: str | int) -> dict[str, Any]:
    """Get details of a BPA role status by ID.

    Role statuses define workflow transitions (e.g., FILE VALIDATED, SEND BACK).

    Args:
        role_status_id: The unique identifier of the role status.

    Returns:
        dict with id, name, type, role_status_type, destination_id, role_id.
    """
    if not role_status_id:
        raise ToolError(
            "Cannot get role status: 'role_status_id' is required. "
            "Use 'role_get' to see statuses for a role."
        )

    try:
        async with BPAClient() as client:
            try:
                status_data = await client.get(
                    "/role_status/{role_status_id}",
                    path_params={"role_status_id": role_status_id},
                    resource_type="role_status",
                    resource_id=role_status_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role status '{role_status_id}' not found. "
                    "Use 'role_get' with a role_id to see available statuses."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="role_status", resource_id=role_status_id
        )

    return _transform_role_status_response(status_data)


async def rolestatus_create(
    role_id: str | int,
    name: str,
    destination_role_id: str | int,
    role_status_type: int = 1,
    message: str | None = None,
) -> dict[str, Any]:
    """Create a user-defined role status. Audited write operation.

    Role statuses control workflow transitions. Types:
    - 1: Forward/approve (goes to next role)
    - 2: Return/revise (goes back to applicant or previous role)

    Args:
        role_id: Role to add status to.
        name: Status name (e.g., "APPROVED", "SEND BACK").
        destination_role_id: Target role ID for this transition.
        role_status_type: 1=forward/approve, 2=return/revise (default: 1).
        message: Optional notification message for this status.

    Returns:
        dict with id, name, role_status_type, destination_id, role_id, audit_id.
    """
    # Pre-flight validation
    if not role_id:
        raise ToolError(
            "Cannot create role status: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )
    if not name or not name.strip():
        raise ToolError("Role status name is required.")
    if not destination_role_id:
        raise ToolError(
            "Cannot create role status: 'destination_role_id' is required. "
            "This is the target role for the workflow transition."
        )
    if role_status_type not in (1, 2):
        raise ToolError("role_status_type must be 1 (forward) or 2 (return).")

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Build payload
    payload: dict[str, Any] = {
        "name": name.strip(),
        "roleStatusType": role_status_type,
        "destinationId": str(destination_role_id),
    }
    if message:
        payload["roleStatusMessage"] = message

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

            # Create audit record BEFORE API call
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="role_status",
                params={"role_id": str(role_id), **payload},
            )

            try:
                status_data = await client.post(
                    "/role/{role_id}/role_status/user_defined_status",
                    path_params={"role_id": role_id},
                    json=payload,
                    resource_type="role_status",
                )

                # Save rollback state
                created_id = status_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="role_status",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "role_id": str(role_id),
                        "name": status_data.get("name"),
                        "_operation": "create",
                    },
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={"id": created_id, "name": status_data.get("name")},
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(e, resource_type="role_status")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)

    result = _transform_role_status_response(status_data)
    result["audit_id"] = audit_id
    return result


async def rolestatus_update(
    role_status_id: str | int,
    name: str | None = None,
    destination_role_id: str | int | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Update a user-defined role status. Audited write operation.

    Args:
        role_status_id: Role status ID to update.
        name: New status name (optional).
        destination_role_id: New target role ID (optional).
        message: New notification message (optional).

    Returns:
        dict with id, name, role_status_type, destination_id, previous_state, audit_id.
    """
    # Pre-flight validation
    if not role_status_id:
        raise ToolError(
            "Cannot update role status: 'role_status_id' is required. "
            "Use 'role_get' to see statuses for a role."
        )

    # At least one field must be provided
    if name is None and destination_role_id is None and message is None:
        raise ToolError("At least one field must be provided for update.")

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    try:
        async with BPAClient() as client:
            # Capture current state for rollback
            try:
                previous_state = await client.get(
                    "/role_status/{role_status_id}",
                    path_params={"role_status_id": role_status_id},
                    resource_type="role_status",
                    resource_id=role_status_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role status '{role_status_id}' not found. "
                    "Use 'role_get' to see available statuses."
                )

            # Merge with current state
            payload: dict[str, Any] = {
                "id": role_status_id,
                "name": name.strip() if name else previous_state.get("name"),
                "roleStatusType": previous_state.get("roleStatusType"),
                "destinationId": (
                    str(destination_role_id)
                    if destination_role_id
                    else previous_state.get("destinationId")
                ),
            }
            if message is not None:
                payload["roleStatusMessage"] = message
            elif previous_state.get("roleStatusMessage"):
                payload["roleStatusMessage"] = previous_state.get("roleStatusMessage")

            # Create audit record
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="role_status",
                object_id=str(role_status_id),
                params={"changes": payload},
            )

            # Save rollback state
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role_status",
                object_id=str(role_status_id),
                previous_state=previous_state,
            )

            try:
                status_data = await client.put(
                    "/role_status/{role_status_id}/user_defined_status",
                    path_params={"role_status_id": role_status_id},
                    json=payload,
                    resource_type="role_status",
                    resource_id=role_status_id,
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={
                        "id": status_data.get("id"),
                        "name": status_data.get("name"),
                    },
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(
                    e, resource_type="role_status", resource_id=role_status_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="role_status", resource_id=role_status_id
        )

    result = _transform_role_status_response(status_data)
    result["previous_state"] = _transform_role_status_response(previous_state)
    result["audit_id"] = audit_id
    return result


async def rolestatus_delete(role_status_id: str | int) -> dict[str, Any]:
    """Delete a role status. Audited write operation.

    Args:
        role_status_id: Role status ID to delete.

    Returns:
        dict with deleted (bool), role_status_id, deleted_status, audit_id.
    """
    if not role_status_id:
        raise ToolError(
            "Cannot delete role status: 'role_status_id' is required. "
            "Use 'role_get' to see statuses for a role."
        )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    try:
        async with BPAClient() as client:
            # Capture current state for rollback
            try:
                previous_state = await client.get(
                    "/role_status/{role_status_id}",
                    path_params={"role_status_id": role_status_id},
                    resource_type="role_status",
                    resource_id=role_status_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Role status '{role_status_id}' not found. "
                    "Use 'role_get' to see available statuses."
                )

            # Create audit record
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="role_status",
                object_id=str(role_status_id),
                params={},
            )

            # Save rollback state
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role_status",
                object_id=str(role_status_id),
                previous_state=previous_state,
            )

            try:
                await client.delete(
                    "/role_status/{role_status_id}",
                    path_params={"role_status_id": role_status_id},
                    resource_type="role_status",
                    resource_id=role_status_id,
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={"deleted": True, "role_status_id": str(role_status_id)},
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(
                    e, resource_type="role_status", resource_id=role_status_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="role_status", resource_id=role_status_id
        )

    return {
        "deleted": True,
        "role_status_id": str(role_status_id),
        "deleted_status": _transform_role_status_response(previous_state),
        "audit_id": audit_id,
    }


def register_role_status_tools(mcp: Any) -> None:
    """Register role status tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(rolestatus_get)
    mcp.tool()(rolestatus_create)
    mcp.tool()(rolestatus_update)
    mcp.tool()(rolestatus_delete)

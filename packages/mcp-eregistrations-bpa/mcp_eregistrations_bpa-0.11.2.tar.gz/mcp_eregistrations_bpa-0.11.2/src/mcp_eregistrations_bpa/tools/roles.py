"""MCP tools for BPA role operations.

This module provides tools for listing, retrieving, creating, updating,
and deleting BPA roles. Roles are access control entities that define
user permissions within a service.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service/{service_id}/role - List roles for a service
- GET /role/{role_id} - Get role by ID
- POST /service/{service_id}/role - Create role within service
- PUT /role - Update role
- DELETE /role/{role_id} - Delete role
- POST /role/{role_id}/role_institution - Assign institution to role
- POST /role/{role_id}/role_registration - Assign registration to role
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
    "role_list",
    "role_get",
    "role_create",
    "role_update",
    "role_delete",
    "roleinstitution_create",
    "roleregistration_create",
    "register_role_tools",
]


def _transform_role_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform role API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        # Core fields
        "id": data.get("id"),
        "name": data.get("name"),
        "short_name": data.get("shortName"),
        "role_type": data.get("type"),
        "assigned_to": data.get("assignedTo"),
        "description": data.get("description"),
        "service_id": data.get("serviceId"),
        # Workflow configuration
        "start_role": data.get("startRole", False),
        "visible_for_applicant": data.get("visibleForApplicant", True),
        "sort_order_number": data.get("sortOrderNumber", 0),
        "used_in_flow": data.get("usedInFlow", False),
        # Permissions
        "allow_to_confirm_payments": data.get("allowToConfirmPayments", False),
        "allow_access_to_financial_reports": data.get(
            "allowAccessToFinancialReports", False
        ),
        # Linked entities (read-only)
        "registrations": data.get("registrations", []),
        "role_institutions": data.get("roleInstitutions", []),
        "statuses": data.get("statuses", []),
        # BotRole-specific fields (only present for BotRole type)
        "repeat_until_successful": data.get("repeatUntilSuccessful"),
        "repeat_in_minutes": data.get("repeatInMinutes"),
        "repeat_in_hours": data.get("repeatInHours"),
        "repeat_in_days": data.get("repeatInDays"),
        "duration_in_minutes": data.get("durationInMinutes"),
        "duration_in_hours": data.get("durationInHours"),
        "duration_in_days": data.get("durationInDays"),
        "bot_role_bots": data.get("botRoleBots"),
        # Audit fields
        "created_by": data.get("createdBy"),
        "created_when": data.get("createdWhen"),
        "last_changed_by": data.get("lastChangedBy"),
        "last_changed_when": data.get("lastChangedWhen"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.roles'",
        "find_by_type": "jq '.roles[] | select(.role_type == \"UserRole\")'",
        "find_by_name": "jq '.roles[] | select(.name | contains(\"search\"))'",
        "start_roles": "jq '.roles[] | select(.start_role == true)'",
    },
)
async def role_list(service_id: str | int) -> dict[str, Any]:
    """List all roles for a BPA service.

    Returns roles configured for the specified service.
    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        service_id: The service ID to list roles for (required).

    Returns:
        dict with roles, service_id, total.
    """
    if not service_id:
        raise ToolError(
            "Cannot list roles: 'service_id' is required. "
            "Use 'service_list' to find valid service IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                roles_data = await client.get_list(
                    "/service/{service_id}/role",
                    path_params={"service_id": service_id},
                    resource_type="role",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role")

    # Transform to consistent output format
    roles = [_transform_role_response(role) for role in roles_data]

    return {
        "roles": roles,
        "service_id": service_id,
        "total": len(roles),
    }


async def _resolve_destination_role_names(
    client: BPAClient, statuses: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Resolve destination IDs in statuses to role names.

    For each status with a destinationId, fetches the destination role
    to get its name. Uses caching to avoid duplicate lookups.

    Args:
        client: Active BPAClient connection.
        statuses: List of status objects from role response.

    Returns:
        list: Enhanced status objects with destination_role_name field.
    """
    if not statuses:
        return []

    # Build mapping of destination_id -> role_name (with caching)
    destination_ids: set[str] = set()
    for status in statuses:
        dest_id = status.get("destinationId")
        if dest_id:
            destination_ids.add(dest_id)

    # Fetch role names for all unique destination IDs
    id_to_name: dict[str, str | None] = {}
    for dest_id in destination_ids:
        try:
            dest_role = await client.get(
                "/role/{role_id}",
                path_params={"role_id": dest_id},
                resource_type="role",
                resource_id=dest_id,
            )
            id_to_name[dest_id] = dest_role.get("name")
        except BPANotFoundError:
            # Graceful fallback: role may have been deleted
            id_to_name[dest_id] = None
        except BPAClientError:
            # Other errors: still graceful fallback
            id_to_name[dest_id] = None

    # Enhance statuses with resolved names
    enhanced_statuses = []
    for status in statuses:
        enhanced = {
            "name": status.get("name"),
            "type": status.get("type"),
        }
        dest_id = status.get("destinationId")
        if dest_id:
            enhanced["destination_id"] = dest_id
            enhanced["destination_role_name"] = id_to_name.get(dest_id)
        enhanced_statuses.append(enhanced)

    return enhanced_statuses


async def role_get(role_id: str | int) -> dict[str, Any]:
    """Get details of a BPA role by ID.

    Returns complete role details with resolved destination role names.

    Args:
        role_id: The unique identifier of the role.

    Returns:
        dict: Complete role details including:
            - id, name, description
            - service_id: The parent service ID
            - statuses: Array with destination_id and destination_role_name resolved
    """
    if not role_id:
        raise ToolError(
            "Cannot get role: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                role_data = await client.get(
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

            # Resolve destination IDs in statuses to role names
            raw_statuses = role_data.get("statuses", [])
            enhanced_statuses = await _resolve_destination_role_names(
                client, raw_statuses
            )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)

    result = _transform_role_response(role_data)
    # Override statuses with enhanced version containing resolved names
    result["statuses"] = enhanced_statuses
    return result


def _validate_role_create_params(
    service_id: str | int,
    name: str,
    short_name: str,
    assigned_to: str,
    role_type: str,
    description: str | None,
    start_role: bool,
    visible_for_applicant: bool,
    sort_order_number: int,
    allow_to_confirm_payments: bool,
    allow_access_to_financial_reports: bool,
    # BotRole-specific parameters
    repeat_until_successful: bool | None,
    repeat_in_minutes: int | None,
    repeat_in_hours: int | None,
    repeat_in_days: int | None,
    duration_in_minutes: int | None,
    duration_in_hours: int | None,
    duration_in_days: int | None,
) -> dict[str, Any]:
    """Validate role_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Role name (required).
        short_name: Short name for the role (required by BPA API).
        assigned_to: Role pool assignment string (e.g., "processing").
        role_type: Role type - "UserRole" for humans, "BotRole" for automation.
        description: Role description (optional).
        start_role: Whether this is the workflow entry point.
        visible_for_applicant: Whether visible to applicants.
        sort_order_number: Ordering in workflow.
        allow_to_confirm_payments: Payment confirmation permission (UserRole only).
        allow_access_to_financial_reports: Financial reports permission (UserRole only).
        repeat_until_successful: Retry on failure (BotRole only).
        repeat_in_minutes: Retry interval in minutes (BotRole only).
        repeat_in_hours: Retry interval in hours (BotRole only).
        repeat_in_days: Retry interval in days (BotRole only).
        duration_in_minutes: Execution timeout in minutes (BotRole only).
        duration_in_hours: Execution timeout in hours (BotRole only).
        duration_in_days: Execution timeout in days (BotRole only).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if not short_name or not short_name.strip():
        errors.append("'short_name' is required and cannot be empty")

    if short_name and len(short_name.strip()) > 50:
        errors.append("'short_name' must be 50 characters or less")

    if not assigned_to or not assigned_to.strip():
        errors.append("'assigned_to' is required and cannot be empty")
    elif len(assigned_to.strip()) < 2:
        errors.append("'assigned_to' must be at least 2 characters")
    elif len(assigned_to.strip()) > 255:
        errors.append("'assigned_to' must be 255 characters or less")

    valid_role_types = ["UserRole", "BotRole"]
    if role_type not in valid_role_types:
        errors.append(f"'role_type' must be one of: {', '.join(valid_role_types)}")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot create role: {error_msg}. Check required fields.")

    params: dict[str, Any] = {
        "name": name.strip(),
        "shortName": short_name.strip(),
        "type": role_type,
        "assignedTo": assigned_to.strip(),
        # Workflow configuration
        "startRole": start_role,
        "visibleForApplicant": visible_for_applicant,
        "sortOrderNumber": sort_order_number,
    }
    if description:
        params["description"] = description.strip()

    # Add role-type-specific parameters
    if role_type == "UserRole":
        # UserRole-specific permissions
        params["allowToConfirmPayments"] = allow_to_confirm_payments
        params["allowAccessToFinancialReports"] = allow_access_to_financial_reports
    elif role_type == "BotRole":
        # BotRole-specific automation configuration
        if repeat_until_successful is not None:
            params["repeatUntilSuccessful"] = repeat_until_successful
        if repeat_in_minutes is not None:
            params["repeatInMinutes"] = repeat_in_minutes
        if repeat_in_hours is not None:
            params["repeatInHours"] = repeat_in_hours
        if repeat_in_days is not None:
            params["repeatInDays"] = repeat_in_days
        if duration_in_minutes is not None:
            params["durationInMinutes"] = duration_in_minutes
        if duration_in_hours is not None:
            params["durationInHours"] = duration_in_hours
        if duration_in_days is not None:
            params["durationInDays"] = duration_in_days

    return params


async def role_create(
    service_id: str | int,
    name: str,
    short_name: str,
    assigned_to: str = "processing",
    role_type: str = "UserRole",
    description: str | None = None,
    start_role: bool = False,
    visible_for_applicant: bool = True,
    sort_order_number: int = 0,
    allow_to_confirm_payments: bool = False,
    allow_access_to_financial_reports: bool = False,
    # BotRole-specific parameters
    repeat_until_successful: bool | None = None,
    repeat_in_minutes: int | None = None,
    repeat_in_hours: int | None = None,
    repeat_in_days: int | None = None,
    duration_in_minutes: int | None = None,
    duration_in_hours: int | None = None,
    duration_in_days: int | None = None,
) -> dict[str, Any]:
    """Create role in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Role name.
        short_name: Short name (required by BPA).
        assigned_to: Role pool (default: "processing").
        role_type: "UserRole" or "BotRole" (default: "UserRole").
        description: Optional description.
        start_role: Workflow entry point (default: False).
        visible_for_applicant: Visible to applicants (default: True).
        sort_order_number: Workflow position (default: 0).
        allow_to_confirm_payments: Payment permission (UserRole only).
        allow_access_to_financial_reports: Reports permission (UserRole only).
        repeat_until_successful: Retry on failure (BotRole only).
        repeat_in_minutes/hours/days: Retry interval (BotRole only).
        duration_in_minutes/hours/days: Execution timeout (BotRole only).

    Returns:
        dict with role details, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_role_create_params(
        service_id,
        name,
        short_name,
        assigned_to,
        role_type,
        description,
        start_role,
        visible_for_applicant,
        sort_order_number,
        allow_to_confirm_payments,
        allow_access_to_financial_reports,
        # BotRole-specific parameters
        repeat_until_successful,
        repeat_in_minutes,
        repeat_in_hours,
        repeat_in_days,
        duration_in_minutes,
        duration_in_hours,
        duration_in_days,
    )

    # Get authenticated user for audit (before any API calls)
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Verify parent service exists before creating audit record
            try:
                await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Cannot create role: Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="role",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                role_data = await client.post(
                    "/service/{service_id}/role",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="role",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = role_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="role",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": role_data.get("name"),
                        "shortName": role_data.get("shortName"),
                        "type": role_data.get("type"),
                        "assignedTo": role_data.get("assignedTo"),
                        "description": role_data.get("description"),
                        "serviceId": str(service_id),
                        # Workflow configuration
                        "startRole": role_data.get("startRole"),
                        "visibleForApplicant": role_data.get("visibleForApplicant"),
                        "sortOrderNumber": role_data.get("sortOrderNumber"),
                        # UserRole permissions
                        "allowToConfirmPayments": role_data.get(
                            "allowToConfirmPayments"
                        ),
                        "allowAccessToFinancialReports": role_data.get(
                            "allowAccessToFinancialReports"
                        ),
                        # BotRole-specific fields
                        "repeatUntilSuccessful": role_data.get("repeatUntilSuccessful"),
                        "repeatInMinutes": role_data.get("repeatInMinutes"),
                        "repeatInHours": role_data.get("repeatInHours"),
                        "repeatInDays": role_data.get("repeatInDays"),
                        "durationInMinutes": role_data.get("durationInMinutes"),
                        "durationInHours": role_data.get("durationInHours"),
                        "durationInDays": role_data.get("durationInDays"),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "role_id": role_data.get("id"),
                        "name": role_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                result = _transform_role_response(role_data)
                result["service_id"] = service_id  # Ensure service_id is always set
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def _validate_role_update_params(
    role_id: str | int,
    name: str | None,
    short_name: str | None,
    assigned_to: str | None,
    description: str | None,
    start_role: bool | None,
    visible_for_applicant: bool | None,
    sort_order_number: int | None,
    allow_to_confirm_payments: bool | None,
    allow_access_to_financial_reports: bool | None,
) -> dict[str, Any]:
    """Validate role_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        role_id: ID of role to update (required).
        name: New name (optional).
        short_name: New short name (optional).
        assigned_to: New role pool assignment string (optional).
        description: New description (optional).
        start_role: Whether this is the workflow entry point (optional).
        visible_for_applicant: Whether visible to applicants (optional).
        sort_order_number: Ordering in workflow (optional).
        allow_to_confirm_payments: Payment confirmation permission (optional).
        allow_access_to_financial_reports: Financial reports permission (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not role_id:
        errors.append("'role_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if short_name is not None and not short_name.strip():
        errors.append("'short_name' cannot be empty when provided")

    if short_name and len(short_name.strip()) > 50:
        errors.append("'short_name' must be 50 characters or less")

    if assigned_to is not None and not assigned_to.strip():
        errors.append("'assigned_to' cannot be empty when provided")

    # At least one field must be provided for update
    all_none = (
        name is None
        and short_name is None
        and assigned_to is None
        and description is None
        and start_role is None
        and visible_for_applicant is None
        and sort_order_number is None
        and allow_to_confirm_payments is None
        and allow_access_to_financial_reports is None
    )
    if all_none:
        errors.append("At least one field must be provided for update")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot update role: {error_msg}. Check required fields.")

    params: dict[str, Any] = {"id": role_id}
    if name is not None:
        params["name"] = name.strip()
    if short_name is not None:
        params["shortName"] = short_name.strip()
    if assigned_to is not None:
        params["assignedTo"] = assigned_to.strip()
    if description is not None:
        params["description"] = description.strip()
    # Workflow configuration
    if start_role is not None:
        params["startRole"] = start_role
    if visible_for_applicant is not None:
        params["visibleForApplicant"] = visible_for_applicant
    if sort_order_number is not None:
        params["sortOrderNumber"] = sort_order_number
    # Permissions
    if allow_to_confirm_payments is not None:
        params["allowToConfirmPayments"] = allow_to_confirm_payments
    if allow_access_to_financial_reports is not None:
        params["allowAccessToFinancialReports"] = allow_access_to_financial_reports

    return params


async def role_update(
    role_id: str | int,
    name: str | None = None,
    short_name: str | None = None,
    assigned_to: str | None = None,
    description: str | None = None,
    start_role: bool | None = None,
    visible_for_applicant: bool | None = None,
    sort_order_number: int | None = None,
    allow_to_confirm_payments: bool | None = None,
    allow_access_to_financial_reports: bool | None = None,
) -> dict[str, Any]:
    """Update an existing BPA role. Audited write operation.

    Args:
        role_id: Role ID to update.
        name: New name (optional).
        short_name: New short name (optional).
        assigned_to: New role pool (optional).
        description: New description (optional).
        start_role: Workflow entry point (optional).
        visible_for_applicant: Visible to applicants (optional).
        sort_order_number: Workflow position (optional).
        allow_to_confirm_payments: Payment permission (optional).
        allow_access_to_financial_reports: Reports permission (optional).

    Returns:
        dict with updated role, previous_state, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_role_update_params(
        role_id,
        name,
        short_name,
        assigned_to,
        description,
        start_role,
        visible_for_applicant,
        sort_order_number,
        allow_to_confirm_payments,
        allow_access_to_financial_reports,
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Capture current state for rollback BEFORE making changes
            try:
                previous_state = await client.get(
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

            # Merge provided changes with current state for full object PUT
            full_params = {
                "id": role_id,
                "name": validated_params.get("name", previous_state.get("name")),
                "shortName": validated_params.get(
                    "shortName", previous_state.get("shortName")
                ),
                "assignedTo": validated_params.get(
                    "assignedTo", previous_state.get("assignedTo")
                ),
                "description": validated_params.get(
                    "description", previous_state.get("description")
                ),
                "serviceId": previous_state.get("serviceId"),
                # Workflow configuration
                "startRole": validated_params.get(
                    "startRole", previous_state.get("startRole", False)
                ),
                "visibleForApplicant": validated_params.get(
                    "visibleForApplicant",
                    previous_state.get("visibleForApplicant", True),
                ),
                "sortOrderNumber": validated_params.get(
                    "sortOrderNumber", previous_state.get("sortOrderNumber", 0)
                ),
                # Permissions
                "allowToConfirmPayments": validated_params.get(
                    "allowToConfirmPayments",
                    previous_state.get("allowToConfirmPayments", False),
                ),
                "allowAccessToFinancialReports": validated_params.get(
                    "allowAccessToFinancialReports",
                    previous_state.get("allowAccessToFinancialReports", False),
                ),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="role",
                object_id=str(role_id),
                params={
                    "changes": validated_params,
                },
            )

            # Save rollback state for undo capability
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role",
                object_id=str(role_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "shortName": previous_state.get("shortName"),
                    "type": previous_state.get("type"),
                    "assignedTo": previous_state.get("assignedTo"),
                    "description": previous_state.get("description"),
                    "serviceId": previous_state.get("serviceId"),
                    # Workflow configuration
                    "startRole": previous_state.get("startRole"),
                    "visibleForApplicant": previous_state.get("visibleForApplicant"),
                    "sortOrderNumber": previous_state.get("sortOrderNumber"),
                    # UserRole permissions
                    "allowToConfirmPayments": previous_state.get(
                        "allowToConfirmPayments"
                    ),
                    "allowAccessToFinancialReports": previous_state.get(
                        "allowAccessToFinancialReports"
                    ),
                    # BotRole-specific fields
                    "repeatUntilSuccessful": previous_state.get(
                        "repeatUntilSuccessful"
                    ),
                    "repeatInMinutes": previous_state.get("repeatInMinutes"),
                    "repeatInHours": previous_state.get("repeatInHours"),
                    "repeatInDays": previous_state.get("repeatInDays"),
                    "durationInMinutes": previous_state.get("durationInMinutes"),
                    "durationInHours": previous_state.get("durationInHours"),
                    "durationInDays": previous_state.get("durationInDays"),
                },
            )

            try:
                role_data = await client.put(
                    "/role",
                    json=full_params,
                    resource_type="role",
                    resource_id=role_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "role_id": role_data.get("id"),
                        "name": role_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                result = _transform_role_response(role_data)
                result["previous_state"] = {
                    "name": previous_state.get("name"),
                    "short_name": previous_state.get("shortName"),
                    "assigned_to": previous_state.get("assignedTo"),
                    "description": previous_state.get("description"),
                    # Workflow configuration
                    "start_role": previous_state.get("startRole"),
                    "visible_for_applicant": previous_state.get("visibleForApplicant"),
                    "sort_order_number": previous_state.get("sortOrderNumber"),
                    # Permissions
                    "allow_to_confirm_payments": previous_state.get(
                        "allowToConfirmPayments"
                    ),
                    "allow_access_to_financial_reports": previous_state.get(
                        "allowAccessToFinancialReports"
                    ),
                }
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role", resource_id=role_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


def _validate_role_delete_params(role_id: str | int) -> None:
    """Validate role_delete parameters (pre-flight).

    Raises ToolError if validation fails.

    Args:
        role_id: Role ID to delete (required).

    Raises:
        ToolError: If validation fails.
    """
    if not role_id:
        raise ToolError(
            "Cannot delete role: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )


async def role_delete(role_id: str | int) -> dict[str, Any]:
    """Delete a BPA role. Audited write operation.

    Known Issue: BPA may return "Camunda publish problem" - contact administrator.

    Args:
        role_id: Role ID to delete.

    Returns:
        dict with deleted (bool), role_id, deleted_role, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_role_delete_params(role_id)

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Use single BPAClient connection for all operations
    try:
        async with BPAClient() as client:
            # Capture current state for rollback BEFORE making changes
            try:
                previous_state = await client.get(
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

            # Normalize previous_state to snake_case for consistency
            normalized_previous_state = {
                "id": previous_state.get("id"),
                "name": previous_state.get("name"),
                "assigned_to": previous_state.get("assignedTo"),
                "description": previous_state.get("description"),
                "service_id": previous_state.get("serviceId"),
                # Workflow configuration
                "start_role": previous_state.get("startRole"),
                "visible_for_applicant": previous_state.get("visibleForApplicant"),
                "sort_order_number": previous_state.get("sortOrderNumber"),
                # Permissions
                "allow_to_confirm_payments": previous_state.get(
                    "allowToConfirmPayments"
                ),
                "allow_access_to_financial_reports": previous_state.get(
                    "allowAccessToFinancialReports"
                ),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="role",
                object_id=str(role_id),
                params={},
            )

            # Save rollback state for undo capability (recreate on rollback)
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="role",
                object_id=str(role_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "shortName": previous_state.get("shortName"),
                    "type": previous_state.get("type"),
                    "assignedTo": previous_state.get("assignedTo"),
                    "description": previous_state.get("description"),
                    "serviceId": previous_state.get("serviceId"),
                    # Workflow configuration
                    "startRole": previous_state.get("startRole"),
                    "visibleForApplicant": previous_state.get("visibleForApplicant"),
                    "sortOrderNumber": previous_state.get("sortOrderNumber"),
                    # UserRole permissions
                    "allowToConfirmPayments": previous_state.get(
                        "allowToConfirmPayments"
                    ),
                    "allowAccessToFinancialReports": previous_state.get(
                        "allowAccessToFinancialReports"
                    ),
                    # BotRole-specific fields
                    "repeatUntilSuccessful": previous_state.get(
                        "repeatUntilSuccessful"
                    ),
                    "repeatInMinutes": previous_state.get("repeatInMinutes"),
                    "repeatInHours": previous_state.get("repeatInHours"),
                    "repeatInDays": previous_state.get("repeatInDays"),
                    "durationInMinutes": previous_state.get("durationInMinutes"),
                    "durationInHours": previous_state.get("durationInHours"),
                    "durationInDays": previous_state.get("durationInDays"),
                },
            )

            try:
                await client.delete(
                    "/role/{role_id}",
                    path_params={"role_id": role_id},
                    resource_type="role",
                    resource_id=role_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "role_id": str(role_id),
                    },
                )

                return {
                    "deleted": True,
                    "role_id": str(role_id),  # Normalize to string for consistency
                    "deleted_role": {
                        "id": normalized_previous_state["id"],
                        "name": normalized_previous_state["name"],
                        "service_id": normalized_previous_state["service_id"],
                    },
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role", resource_id=role_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


async def roleinstitution_create(
    role_id: str | int,
    institution_id: str,
) -> dict[str, Any]:
    """Assign institution to a role. Audited write operation. Required for publishing.

    Args:
        role_id: Role to assign institution to.
        institution_id: Institution to assign.

    Returns:
        dict with id, role_id, institution_id, audit_id.
    """
    # Pre-flight validation (no audit if these fail)
    if not role_id:
        raise ToolError(
            "Cannot create role institution: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )
    if not institution_id:
        raise ToolError(
            "Cannot create role institution: 'institution_id' is required. "
            "Use 'institution_discover' to find valid institution IDs."
        )

    # Get user email for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Verify role exists (no audit if not found)
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
                object_type="role_institution",
                params={
                    "role_id": str(role_id),
                    "institution_id": institution_id,
                },
            )

            # Execute API call - body is the raw institution_id string
            try:
                result = await client.post(
                    "/role/{role_id}/role_institution",
                    path_params={"role_id": role_id},
                    content=institution_id,  # Raw string body
                    resource_type="role_institution",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "role_id": str(role_id),
                        "institution_id": institution_id,
                    },
                )

                # Transform response
                return {
                    "id": result.get("id") if isinstance(result, dict) else None,
                    "role_id": str(role_id),
                    "institution_id": institution_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role_institution")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


async def roleregistration_create(
    role_id: str | int,
    registration_id: str | int,
) -> dict[str, Any]:
    """Assign registration to a role. Audited write operation. Required for publishing.

    Args:
        role_id: Role to assign registration to.
        registration_id: Registration to assign.

    Returns:
        dict with id, role_id, registration_id, audit_id.
    """
    # Pre-flight validation (no audit if these fail)
    if not role_id:
        raise ToolError(
            "Cannot create role registration: 'role_id' is required. "
            "Use 'role_list' with service_id to find valid role IDs."
        )
    if not registration_id:
        raise ToolError(
            "Cannot create role registration: 'registration_id' is required. "
            "Use 'registration_list' with service_id to find valid registration IDs."
        )

    # Get user email for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Verify role exists (no audit if not found)
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
                object_type="role_registration",
                params={
                    "role_id": str(role_id),
                    "registration_id": str(registration_id),
                },
            )

            # Execute API call - body is the raw registration_id string
            try:
                result = await client.post(
                    "/role/{role_id}/role_registration",
                    path_params={"role_id": role_id},
                    content=str(
                        registration_id
                    ),  # Raw string body like role_institution
                    resource_type="role_registration",
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "role_id": str(role_id),
                        "registration_id": str(registration_id),
                    },
                )

                # Transform response
                return {
                    "id": result.get("id") if isinstance(result, dict) else None,
                    "role_id": str(role_id),
                    "registration_id": str(registration_id),
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="role_registration")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="role", resource_id=role_id)


def register_role_tools(mcp: Any) -> None:
    """Register role tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(role_list)
    mcp.tool()(role_get)
    # Write operations (audit-before-write pattern)
    mcp.tool()(role_create)
    mcp.tool()(role_update)
    # Role assignment tools (required for publishing)
    mcp.tool()(roleinstitution_create)
    mcp.tool()(roleregistration_create)
    # NOTE: role_delete disabled due to Camunda server-side 404 error.
    # The BPA server returns "Camunda publish problem" when deleting roles.
    # Re-enable when the server-side issue is resolved.
    # mcp.tool()(role_delete)

"""MCP tools for BPA registration institution operations.

This module provides tools for listing, retrieving, creating, and deleting
registration institution assignments. Registration institutions link a
registration to an institution, which is required for publishing services.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /registration/{registration_id}/registration_institution - List for registration
- POST /registration/{registration_id}/registration_institution - Create assignment
- GET /registration_institution/{registration_institution_id} - Get by ID
- DELETE /registration_institution/{registration_institution_id} - Delete assignment
- GET /registration_institution_by_institution/{institution_id} - List by institution
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.audit.context import (
    NotAuthenticatedError,
    get_current_user_email,
    get_token_manager,
)
from mcp_eregistrations_bpa.audit.logger import AuditLogger
from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)
from mcp_eregistrations_bpa.config import load_config
from mcp_eregistrations_bpa.tools.large_response import large_response_handler

__all__ = [
    "registrationinstitution_list",
    "registrationinstitution_get",
    "registrationinstitution_create",
    "registrationinstitution_delete",
    "registrationinstitution_list_by_institution",
    "institution_discover",
    "institution_create",
    "register_registration_institution_tools",
]

# Default institutions parent group ID in Keycloak
# Can be overridden with KEYCLOAK_INSTITUTIONS_GROUP_ID env var
DEFAULT_INSTITUTIONS_PARENT_GROUP = "967d3d31-5114-4131-b7e1-f5c652227259"


def _transform_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform registration institution API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "registration_id": data.get("registrationId"),
        "institution_id": data.get("institutionId"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.assignments'",
        "by_institution": "jq '.assignments[] | select(.institution_id==\"x\")'",
    },
)
async def registrationinstitution_list(
    registration_id: str | int,
) -> dict[str, Any]:
    """List institution assignments for a registration.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        registration_id: Registration ID to list assignments for.

    Returns:
        dict with assignments, registration_id, total.
    """
    if not registration_id:
        raise ToolError(
            "Cannot list registration institutions: 'registration_id' is required. "
            "Use 'registration_list' to find valid registration IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                data = await client.get_list(
                    "/registration/{registration_id}/registration_institution",
                    path_params={"registration_id": registration_id},
                    resource_type="registration_institution",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Registration '{registration_id}' not found. "
                    "Use 'registration_list' to see available registrations."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="registration_institution")

    # Transform to consistent output format
    assignments = [_transform_response(item) for item in data]

    return {
        "assignments": assignments,
        "registration_id": registration_id,
        "total": len(assignments),
    }


async def registrationinstitution_get(
    registration_institution_id: str | int,
) -> dict[str, Any]:
    """Get registration institution assignment by ID.

    Args:
        registration_institution_id: Assignment ID.

    Returns:
        dict with id, registration_id, institution_id.
    """
    if not registration_institution_id:
        raise ToolError(
            "Cannot get registration institution: "
            "'registration_institution_id' is required."
        )

    try:
        async with BPAClient() as client:
            try:
                data = await client.get(
                    "/registration_institution/{registration_institution_id}",
                    path_params={
                        "registration_institution_id": registration_institution_id
                    },
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Registration institution '{registration_institution_id}' "
                    "not found."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="registration_institution")

    return _transform_response(data)


async def registrationinstitution_create(
    registration_id: str | int,
    institution_id: str,
) -> dict[str, Any]:
    """Assign institution to registration. Audited write operation.

    Required for publishing services.

    Args:
        registration_id: Registration ID to assign institution to.
        institution_id: Institution ID to assign.

    Returns:
        dict with id, registration_id, institution_id, audit_id.
    """
    # Pre-flight validation (no audit if these fail)
    if not registration_id:
        raise ToolError(
            "Cannot create registration institution: 'registration_id' is required. "
            "Use 'registration_list' to find valid registration IDs."
        )
    if not institution_id:
        raise ToolError(
            "Cannot create registration institution: 'institution_id' is required."
        )

    # Get user email for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError:
        raise ToolError(
            "Authentication required to create registration institution assignment. "
            "Use 'auth_login' to authenticate first."
        )

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Verify registration exists (no audit if not found)
            try:
                await client.get(
                    "/registration/{registration_id}",
                    path_params={"registration_id": registration_id},
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Registration '{registration_id}' not found. "
                    "Use 'registration_list' to see available registrations."
                )

            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="registration_institution",
                params={
                    "registration_id": registration_id,
                    "institution_id": institution_id,
                },
            )

            # Execute API call - body is the raw institution_id string
            try:
                result = await client.post(
                    "/registration/{registration_id}/registration_institution",
                    path_params={"registration_id": registration_id},
                    content=institution_id,
                )

                # Mark audit success
                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result=result,
                )

            except Exception as e:
                # Mark audit failed
                await audit_logger.mark_failed(
                    audit_id=audit_id,
                    error_message=str(e),
                )
                raise

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="registration_institution")

    response = _transform_response(result)
    response["audit_id"] = audit_id
    return response


async def registrationinstitution_delete(
    registration_institution_id: str | int,
) -> dict[str, Any]:
    """Delete registration institution assignment. Audited write operation.

    Saves state before deletion; use rollback with audit_id to restore.

    Args:
        registration_institution_id: Assignment ID to delete.

    Returns:
        dict with deleted (bool), registration_institution_id, deleted_assignment,
        audit_id.
    """
    # Pre-flight validation
    if not registration_institution_id:
        raise ToolError(
            "Cannot delete registration institution: "
            "'registration_institution_id' is required."
        )

    # Get user email for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError:
        raise ToolError(
            "Authentication required to delete registration institution assignment. "
            "Use 'auth_login' to authenticate first."
        )

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Capture current state for rollback
            try:
                current_state = await client.get(
                    "/registration_institution/{registration_institution_id}",
                    path_params={
                        "registration_institution_id": registration_institution_id
                    },
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Registration institution '{registration_institution_id}' "
                    "not found."
                )

            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="registration_institution",
                object_id=str(registration_institution_id),
                params={"registration_institution_id": registration_institution_id},
            )

            # Save rollback state separately
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="registration_institution",
                object_id=str(registration_institution_id),
                previous_state=current_state,
            )

            # Execute delete
            try:
                await client.delete(
                    "/registration_institution/{registration_institution_id}",
                    path_params={
                        "registration_institution_id": registration_institution_id
                    },
                )

                # Mark audit success
                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={"deleted": True},
                )

            except Exception as e:
                # Mark audit failed
                await audit_logger.mark_failed(
                    audit_id=audit_id,
                    error_message=str(e),
                )
                raise

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="registration_institution")

    return {
        "deleted": True,
        "registration_institution_id": registration_institution_id,
        "deleted_assignment": _transform_response(current_state),
        "audit_id": audit_id,
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.assignments'",
        "by_registration": "jq '.assignments[] | select(.registration_id==\"x\")'",
    },
)
async def registrationinstitution_list_by_institution(
    institution_id: str,
) -> dict[str, Any]:
    """List registration assignments for an institution.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        institution_id: Institution ID to list registrations for.

    Returns:
        dict with assignments, institution_id, total.
    """
    if not institution_id:
        raise ToolError("Cannot list by institution: 'institution_id' is required.")

    try:
        async with BPAClient() as client:
            try:
                data = await client.get_list(
                    "/registration_institution_by_institution/{institution_id}",
                    path_params={"institution_id": institution_id},
                    resource_type="registration_institution",
                )
            except BPANotFoundError:
                # Institution may have no assignments
                data = []
    except BPAClientError as e:
        raise translate_error(e, resource_type="registration_institution")

    # Transform to consistent output format
    assignments = [_transform_response(item) for item in data]

    return {
        "assignments": assignments,
        "institution_id": institution_id,
        "total": len(assignments),
    }


async def institution_discover(
    sample_size: int = 50,
) -> dict[str, Any]:
    """Discover institution IDs by scanning existing registrations.

    BPA lacks a direct institution list endpoint. This queries registrations
    sequentially, so response time scales with sample_size.

    Args:
        sample_size: Registrations to sample (default 50).

    Returns:
        dict with institutions, total, registrations_scanned,
        registrations_with_institutions, message.
    """
    try:
        async with BPAClient() as client:
            # Get list of registrations
            try:
                registrations = await client.get_list(
                    "/registration",
                    resource_type="registration",
                )
            except BPANotFoundError:
                return {
                    "institutions": [],
                    "total": 0,
                    "registrations_scanned": 0,
                    "registrations_with_institutions": 0,
                    "message": "No registrations found in the system.",
                }

            # Limit to sample size
            sample = registrations[:sample_size]

            # Collect unique institution IDs
            institution_ids: set[str] = set()
            registrations_with_institutions = 0

            for reg in sample:
                reg_id = reg.get("id")
                if not reg_id:
                    continue

                try:
                    assignments = await client.get_list(
                        "/registration/{registration_id}/registration_institution",
                        path_params={"registration_id": reg_id},
                        resource_type="registration_institution",
                    )

                    if assignments:
                        registrations_with_institutions += 1
                        for assignment in assignments:
                            inst_id = assignment.get("institutionId")
                            if inst_id:
                                institution_ids.add(inst_id)
                except BPANotFoundError:
                    # Registration may have been deleted
                    continue
                except Exception:
                    # Skip problematic registrations
                    continue

            institutions_list = sorted(institution_ids)

            if not institutions_list:
                message = (
                    f"Scanned {len(sample)} registrations but found no institution "
                    "assignments. Institution IDs may need to be obtained from "
                    "your BPA administrator."
                )
            else:
                message = (
                    f"Found {len(institutions_list)} unique institution(s) from "
                    f"{registrations_with_institutions} assigned registrations. "
                    f"Use any of these IDs with registrationinstitution_create."
                )

            return {
                "institutions": institutions_list,
                "total": len(institutions_list),
                "registrations_scanned": len(sample),
                "registrations_with_institutions": registrations_with_institutions,
                "message": message,
            }

    except BPAClientError as e:
        raise translate_error(e, resource_type="institution")


async def institution_create(
    name: str,
    short_name: str,
    url: str | None = None,
) -> dict[str, Any]:
    """Create institution in Keycloak. Audited write operation.

    Creates Keycloak group under institutions parent. Configure parent via
    KEYCLOAK_INSTITUTIONS_GROUP_ID env var.

    Args:
        name: Institution display name.
        short_name: Short name/abbreviation.
        url: Optional website URL.

    Returns:
        dict with id, name, short_name, url, path, audit_id.
    """
    # Pre-flight validation
    if not name or not name.strip():
        raise ToolError("Cannot create institution: 'name' is required.")
    if not short_name or not short_name.strip():
        raise ToolError("Cannot create institution: 'short_name' is required.")

    name = name.strip()
    short_name = short_name.strip()

    # Get user email for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError:
        raise ToolError(
            "Authentication required to create institution. "
            "Use 'auth_login' to authenticate first."
        )

    # Get token manager for Keycloak API calls
    token_manager = get_token_manager()

    # Load config to get Keycloak URL and realm
    config = load_config()
    if not config.keycloak_url or not config.keycloak_realm:
        raise ToolError(
            "Keycloak configuration required for institution management. "
            "Set KEYCLOAK_URL and KEYCLOAK_REALM environment variables."
        )

    # Get parent group ID from env or use default
    parent_group_id = os.environ.get(
        "KEYCLOAK_INSTITUTIONS_GROUP_ID", DEFAULT_INSTITUTIONS_PARENT_GROUP
    )

    audit_logger = AuditLogger()

    # Prepare request payload
    attributes: dict[str, list[str]] = {
        "shortName": [short_name],
    }
    if url:
        attributes["url"] = [url]

    payload = {
        "name": name,
        "attributes": attributes,
    }

    # Create PENDING audit record
    audit_id = await audit_logger.record_pending(
        user_email=user_email,
        operation_type="create",
        object_type="institution",
        params={
            "name": name,
            "short_name": short_name,
            "url": url,
            "parent_group_id": parent_group_id,
        },
    )

    try:
        # Get access token
        access_token = await token_manager.get_access_token()

        # Build Keycloak Admin API URL
        keycloak_url = (
            f"{config.keycloak_url}/admin/realms/{config.keycloak_realm}"
            f"/groups/{parent_group_id}/children"
        )

        # Make the request to Keycloak
        async with httpx.AsyncClient() as client:
            response = await client.post(
                keycloak_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            if response.status_code == 409:
                await audit_logger.mark_failed(audit_id, "Institution already exists")
                raise ToolError(
                    f"Institution '{name}' already exists. "
                    "Use 'institution_discover' to find existing institutions."
                )

            if response.status_code == 403:
                await audit_logger.mark_failed(audit_id, "Permission denied")
                raise ToolError(
                    "Permission denied to create institution. "
                    "Ensure your account has Keycloak admin privileges."
                )

            if response.status_code == 404:
                await audit_logger.mark_failed(audit_id, "Parent group not found")
                raise ToolError(
                    f"Institutions parent group '{parent_group_id}' not found. "
                    "Check KEYCLOAK_INSTITUTIONS_GROUP_ID configuration."
                )

            response.raise_for_status()
            result = response.json()

        # Mark audit success
        await audit_logger.mark_success(
            audit_id=audit_id,
            result={"id": result.get("id"), **result},
        )

        # Return formatted response
        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "short_name": short_name,
            "url": url,
            "path": result.get("path"),
            "audit_id": audit_id,
            "message": (
                f"Institution '{name}' created successfully. "
                "Use this ID with registrationinstitution_create to assign."
            ),
        }

    except ToolError:
        raise
    except httpx.HTTPStatusError as e:
        error_msg = f"Keycloak API error: {e.response.status_code}"
        try:
            error_detail = e.response.json()
            if "errorMessage" in error_detail:
                error_msg = f"Keycloak error: {error_detail['errorMessage']}"
        except Exception:
            pass
        await audit_logger.mark_failed(audit_id, error_msg)
        raise ToolError(error_msg)
    except httpx.RequestError as e:
        error_msg = f"Network error connecting to Keycloak: {e}"
        await audit_logger.mark_failed(audit_id, error_msg)
        raise ToolError(error_msg)
    except Exception as e:
        await audit_logger.mark_failed(audit_id, str(e))
        raise ToolError(f"Failed to create institution: {e}")


def register_registration_institution_tools(mcp_server: Any) -> None:
    """Register registration institution tools with the MCP server.

    Args:
        mcp_server: The FastMCP server instance.
    """
    mcp_server.tool()(registrationinstitution_list)
    mcp_server.tool()(registrationinstitution_get)
    mcp_server.tool()(registrationinstitution_create)
    mcp_server.tool()(registrationinstitution_delete)
    mcp_server.tool()(registrationinstitution_list_by_institution)
    mcp_server.tool()(institution_discover)
    mcp_server.tool()(institution_create)

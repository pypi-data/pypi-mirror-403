"""MCP tools for BPA classification/catalog operations.

This module provides tools for listing, retrieving, creating, and updating
BPA classifications (catalog data sources used for dropdown fields in forms).

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED
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
    "classification_list",
    "classification_get",
    "classification_create",
    "classification_update",
    "classification_export_csv",
    "register_classification_tools",
]


def _transform_classification_summary(classification: dict[str, Any]) -> dict[str, Any]:
    """Transform classification to summary format with snake_case keys."""
    return {
        "id": classification.get("id"),
        "name": classification.get("name"),
        "type": classification.get("type") or classification.get("classificationType"),
        "entry_count": (
            classification.get("entryCount") or classification.get("size", 0)
        ),
    }


def _transform_classification_detail(classification: dict[str, Any]) -> dict[str, Any]:
    """Transform classification to detailed format with entries."""
    # Handle entries - may be in 'content' (pageable) or 'entries' field
    raw_entries = classification.get("content") or classification.get("entries") or []
    entries = []
    for entry in raw_entries:
        entries.append(
            {
                "value": entry.get("value") or entry.get("key"),
                "label": entry.get("label") or entry.get("name") or entry.get("value"),
            }
        )

    return {
        "id": classification.get("id"),
        "name": classification.get("name"),
        "type": classification.get("type") or classification.get("classificationType"),
        "entries": entries,
        "entry_count": len(entries),
        "created_at": classification.get("createdAt"),
        "updated_at": classification.get("updatedAt"),
    }


async def classification_list(
    limit: int = 50,
    offset: int = 0,
    name_filter: str | None = None,
) -> dict[str, Any]:
    """List all classifications (catalog data sources).

    Args:
        limit: Maximum to return (default: 50).
        offset: Skip count (default: 0).
        name_filter: Filter by name (contains, case-insensitive).

    Returns:
        dict with classifications, total, has_more.
    """
    # Normalize pagination parameters
    if limit <= 0:
        limit = 50
    if offset < 0:
        offset = 0

    try:
        async with BPAClient() as client:
            classifications_data = await client.get_list(
                "/classification",
                resource_type="classification",
            )
    except BPAClientError as e:
        raise translate_error(e, resource_type="classification")

    # Transform to consistent output format with snake_case keys
    all_classifications = [
        _transform_classification_summary(c) for c in classifications_data
    ]

    # Apply name filter if provided
    if name_filter:
        name_filter_lower = name_filter.lower()
        all_classifications = [
            c
            for c in all_classifications
            if name_filter_lower in (c.get("name") or "").lower()
        ]

    # Sort by name for consistent pagination ordering
    all_classifications.sort(key=lambda c: c.get("name") or "")

    # Calculate total before pagination
    total = len(all_classifications)

    # Apply pagination
    paginated = all_classifications[offset : offset + limit]

    # Calculate has_more
    has_more = (offset + limit) < total

    return {
        "classifications": paginated,
        "total": total,
        "has_more": has_more,
    }


@large_response_handler(
    navigation={
        "list_entries": "jq '.entries'",
        "find_by_value": "jq '.entries[] | select(.value == \"CODE\")'",
        "find_by_label": "jq '.entries[] | select(.label | contains(\"search\"))'",
        "entry_count": "jq '.entry_count'",
    }
)
async def classification_get(classification_id: str | int) -> dict[str, Any]:
    """Get classification details by ID including entries.

    Large responses (>100KB) are saved to file with navigation hints.

    Args:
        classification_id: The classification ID.

    Returns:
        dict with id, name, type, entries, entry_count, created_at, updated_at.
    """
    try:
        async with BPAClient() as client:
            try:
                # Use pageable endpoint to get entries
                classification_data = await client.get(
                    "/classification/{id}/pageable",
                    path_params={"id": classification_id},
                    resource_type="classification",
                    resource_id=classification_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Classification '{classification_id}' not found. "
                    "Use 'classification_list' to see available classifications."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="classification", resource_id=classification_id
        )

    return _transform_classification_detail(classification_data)


def _validate_classification_create_params(
    classification_type_id: str,
    name: str,
    entries: list[dict[str, str]],
) -> dict[str, Any]:
    """Validate classification_create parameters (pre-flight).

    Args:
        classification_type_id: The type of classification to create.
        name: The classification name.
        entries: List of entries with value and label.

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not classification_type_id or not classification_type_id.strip():
        errors.append("'classification_type_id' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if not entries:
        errors.append("'entries' must contain at least one entry")

    # Validate entry structure
    for i, entry in enumerate(entries or []):
        if not isinstance(entry, dict):
            errors.append(f"Entry {i} must be a dict with 'value' and 'label'")
            continue
        if not entry.get("value"):
            errors.append(f"Entry {i} missing required 'value' field")
        if not entry.get("label"):
            errors.append(f"Entry {i} missing required 'label' field")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create classification: {error_msg}. Check required fields."
        )

    # Build API payload
    formatted_entries = [{"value": e["value"], "label": e["label"]} for e in entries]

    return {
        "name": name.strip(),
        "entries": formatted_entries,
    }


async def classification_create(
    classification_type_id: str,
    name: str,
    entries: list[dict[str, str]],
) -> dict[str, Any]:
    """Create a classification catalog. Audited write operation.

    Args:
        classification_type_id: The type ID for the classification.
        name: The classification name.
        entries: List of entries, each with 'value' and 'label' keys.

    Returns:
        dict with id, name, type, entries, entry_count, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_classification_create_params(
        classification_type_id, name, entries
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    try:
        async with BPAClient() as client:
            # Create audit record BEFORE API call
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="classification",
                params={
                    "classification_type_id": classification_type_id,
                    **validated_params,
                },
            )

            try:
                classification_data = await client.post(
                    "/classification/{classification_type_id}",
                    path_params={"classification_type_id": classification_type_id},
                    json=validated_params,
                    resource_type="classification",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = classification_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="classification",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": classification_data.get("name"),
                        "type": classification_data.get("type"),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "classification_id": created_id,
                        "name": classification_data.get("name"),
                    },
                )

                result = _transform_classification_detail(classification_data)
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="classification")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="classification")


def _validate_classification_update_params(
    classification_id: str | int,
    name: str | None,
    entries: list[dict[str, str]] | None,
) -> dict[str, Any]:
    """Validate classification_update parameters (pre-flight).

    Args:
        classification_id: The classification ID to update.
        name: New name (optional).
        entries: New entries list (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not classification_id:
        errors.append("'classification_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    # Validate entry structure if provided
    if entries is not None:
        if not entries:
            errors.append("'entries' cannot be empty when provided")
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"Entry {i} must be a dict with 'value' and 'label'")
                continue
            if not entry.get("value"):
                errors.append(f"Entry {i} missing required 'value' field")
            if not entry.get("label"):
                errors.append(f"Entry {i} missing required 'label' field")

    # At least one field must be provided
    if name is None and entries is None:
        errors.append("At least one of 'name' or 'entries' must be provided")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot update classification: {error_msg}. Check required fields."
        )

    # Build API payload with only provided fields
    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name.strip()
    if entries is not None:
        params["entries"] = [
            {"value": e["value"], "label": e["label"]} for e in entries
        ]

    return params


async def classification_update(
    classification_id: str | int,
    name: str | None = None,
    entries: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Update a classification catalog. Audited write operation.

    Args:
        classification_id: The classification ID to update.
        name: New name (optional).
        entries: New entries list (optional).

    Returns:
        dict with id, name, type, entries, entry_count, audit_id.
    """
    # Pre-flight validation
    validated_params = _validate_classification_update_params(
        classification_id, name, entries
    )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    try:
        async with BPAClient() as client:
            # Fetch current state for rollback
            try:
                current_data = await client.get(
                    "/classification/{id}/pageable",
                    path_params={"id": classification_id},
                    resource_type="classification",
                    resource_id=classification_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Classification '{classification_id}' not found. "
                    "Use 'classification_list' to see available classifications."
                )

            # Create audit record BEFORE API call
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="classification",
                object_id=str(classification_id),
                params=validated_params,
            )

            try:
                # Add id to payload for PUT request
                update_payload = {"id": classification_id, **validated_params}

                classification_data = await client.put(
                    "/classification/{id}",
                    path_params={"id": classification_id},
                    json=update_payload,
                    resource_type="classification",
                    resource_id=classification_id,
                )

                # Save rollback state (previous state for restore)
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="classification",
                    object_id=str(classification_id),
                    previous_state={
                        "id": current_data.get("id"),
                        "name": current_data.get("name"),
                        "type": current_data.get("type"),
                        "entries": current_data.get("content")
                        or current_data.get("entries"),
                        "_operation": "update",
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "classification_id": classification_id,
                        "name": classification_data.get("name"),
                    },
                )

                result = _transform_classification_detail(classification_data)
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="classification", resource_id=classification_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="classification", resource_id=classification_id
        )


async def classification_export_csv(classification_id: str | int) -> dict[str, Any]:
    """Export classification entries as CSV content.

    Args:
        classification_id: The classification ID to export.

    Returns:
        dict with classification_id, name, csv_content, entry_count.
    """
    try:
        async with BPAClient() as client:
            try:
                # First get classification details for metadata
                classification_data = await client.get(
                    "/classification/{id}/pageable",
                    path_params={"id": classification_id},
                    resource_type="classification",
                    resource_id=classification_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Classification '{classification_id}' not found. "
                    "Use 'classification_list' to see available classifications."
                )

            # Get CSV export
            try:
                csv_response = await client.get(
                    "/classification/{id}/exportCsv",
                    path_params={"id": classification_id},
                    resource_type="classification",
                    resource_id=classification_id,
                )
            except BPAClientError as e:
                raise translate_error(
                    e, resource_type="classification", resource_id=classification_id
                )

            # The response may be raw CSV text or a dict with content
            if isinstance(csv_response, str):
                csv_content = csv_response
            elif isinstance(csv_response, dict):
                csv_content = csv_response.get("content", str(csv_response))
            else:
                csv_content = str(csv_response)

            # Count entries from original data
            raw_entries = (
                classification_data.get("content")
                or classification_data.get("entries")
                or []
            )

            return {
                "classification_id": classification_id,
                "name": classification_data.get("name"),
                "csv_content": csv_content,
                "entry_count": len(raw_entries),
            }

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="classification", resource_id=classification_id
        )


def register_classification_tools(mcp: Any) -> None:
    """Register classification tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(classification_list)
    mcp.tool()(classification_get)
    mcp.tool()(classification_create)
    mcp.tool()(classification_update)
    mcp.tool()(classification_export_csv)

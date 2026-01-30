"""MCP tools for BPA message operations.

Messages are reusable email/SMS/WhatsApp templates. Unlike notifications
(service-scoped), messages are global and can be linked to roles.

Write operations follow the audit-before-write pattern.

API Endpoints used:
- GET /message - List messages (paginated)
- GET /message/{message_id} - Get message by ID
- POST /message - Create message
- PUT /message - Update message
- DELETE /message/{message_id} - Delete message
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
    "message_list",
    "message_get",
    "message_create",
    "message_update",
    "message_delete",
    "register_message_tools",
]


def _transform_message_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform message API response from camelCase to snake_case.

    Based on Message model from BPA frontend:
    - id, name, code, subject, content
    - messageType (MESSAGE/ALERT), channel (EMAIL/SMS/WHATSAPP)
    - businessKey, roleRegistrations, messageRoleStatuses, messageBots

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "code": data.get("code"),
        "subject": data.get("subject"),
        "content": data.get("content"),
        "message_type": data.get("messageType"),
        "channel": data.get("channel"),
        "business_key": data.get("businessKey"),
        "role_registrations": data.get("roleRegistrations"),
        "message_role_statuses": data.get("messageRoleStatuses"),
        "message_bots": data.get("messageBots"),
        # Audit fields
        "created_by": data.get("createdBy"),
        "created_when": data.get("createdWhen"),
        "last_changed_by": data.get("lastChangedBy"),
        "last_changed_when": data.get("lastChangedWhen"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.messages'",
        "find_by_channel": "jq '.messages[] | select(.channel == \"EMAIL\")'",
        "find_by_type": "jq '.messages[] | select(.message_type == \"MESSAGE\")'",
        "find_by_name": "jq '.messages[] | select(.name | contains(\"search\"))'",
    },
)
async def message_list(
    page: int = 0,
    size: int = 50,
    channel: str | None = None,
    name_filter: str | None = None,
) -> dict[str, Any]:
    """List BPA messages (global reusable templates).

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        page: Page number, 0-indexed (default: 0).
        size: Page size (default: 50).
        channel: Filter by channel: EMAIL, SMS, WHATSAPP (optional).
        name_filter: Filter by name substring (optional).

    Returns:
        dict with messages, total, page, size, has_more.
    """
    if page < 0:
        page = 0
    if size <= 0:
        size = 50

    try:
        async with BPAClient() as client:
            # Build query params for pagination
            params: dict[str, Any] = {
                "page": page,
                "size": size,
            }
            if channel:
                params["channel"] = channel.upper()
            if name_filter:
                params["filter"] = name_filter

            messages_data = await client.get_list(
                "/message",
                params=params,
                resource_type="message",
            )
    except BPAClientError as e:
        raise translate_error(e, resource_type="message")

    messages = [_transform_message_response(m) for m in messages_data]

    return {
        "messages": messages,
        "total": len(messages),
        "page": page,
        "size": size,
        "has_more": len(messages) == size,
    }


async def message_get(message_id: str) -> dict[str, Any]:
    """Get a BPA message by ID.

    Args:
        message_id: The message ID.

    Returns:
        dict with id, name, code, subject, content, message_type, channel.
    """
    if not message_id:
        raise ToolError(
            "Cannot get message: 'message_id' is required. "
            "Use 'message_list' to find valid IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                message_data = await client.get(
                    "/message/{message_id}",
                    path_params={"message_id": message_id},
                    resource_type="message",
                    resource_id=message_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Message '{message_id}' not found. "
                    "Use 'message_list' to see available messages."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="message", resource_id=message_id)

    return _transform_message_response(message_data)


async def message_create(
    name: str,
    channel: str = "EMAIL",
    message_type: str = "MESSAGE",
    subject: str | None = None,
    content: str | None = None,
    code: str | None = None,
) -> dict[str, Any]:
    """Create a BPA message template. Audited write operation.

    Args:
        name: Message name (required).
        channel: EMAIL, SMS, or WHATSAPP (default: EMAIL).
        message_type: MESSAGE or ALERT (default: MESSAGE).
        subject: Email subject line (optional).
        content: Message body/template (optional).
        code: Unique code identifier (optional).

    Returns:
        dict with id, name, channel, message_type, audit_id.
    """
    # Pre-flight validation
    if not name or not name.strip():
        raise ToolError("Message name is required.")

    channel = (channel or "EMAIL").upper()
    if channel not in ("EMAIL", "SMS", "WHATSAPP"):
        raise ToolError("Channel must be EMAIL, SMS, or WHATSAPP.")

    message_type = (message_type or "MESSAGE").upper()
    if message_type not in ("MESSAGE", "ALERT"):
        raise ToolError("Message type must be MESSAGE or ALERT.")

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Build payload matching BPA Message model
    payload: dict[str, Any] = {
        "name": name.strip(),
        "channel": channel,
        "messageType": message_type,
    }
    if subject:
        payload["subject"] = subject
    if content:
        payload["content"] = content
    if code:
        payload["code"] = code

    audit_logger = AuditLogger()

    try:
        async with BPAClient() as client:
            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="message",
                params=payload,
            )

            try:
                message_data = await client.post(
                    "/message",
                    json=payload,
                    resource_type="message",
                )

                # Save rollback state
                created_id = message_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="message",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": message_data.get("name"),
                        "_operation": "create",
                    },
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={"id": created_id, "name": message_data.get("name")},
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(e, resource_type="message")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="message")

    result = _transform_message_response(message_data)
    result["audit_id"] = audit_id
    return result


async def message_update(
    message_id: str,
    name: str | None = None,
    subject: str | None = None,
    content: str | None = None,
    channel: str | None = None,
    message_type: str | None = None,
    code: str | None = None,
) -> dict[str, Any]:
    """Update a BPA message. Audited write operation.

    Args:
        message_id: Message ID to update (required).
        name: New message name (optional).
        subject: New subject line (optional).
        content: New message body (optional).
        channel: New channel: EMAIL, SMS, WHATSAPP (optional).
        message_type: New type: MESSAGE, ALERT (optional).
        code: New code identifier (optional).

    Returns:
        dict with id, name, channel, previous_state, audit_id.
    """
    if not message_id:
        raise ToolError(
            "Cannot update message: 'message_id' is required. "
            "Use 'message_list' to find valid IDs."
        )

    # At least one field must be provided
    if all(v is None for v in [name, subject, content, channel, message_type, code]):
        raise ToolError("At least one field must be provided for update.")

    # Validate channel if provided
    if channel:
        channel = channel.upper()
        if channel not in ("EMAIL", "SMS", "WHATSAPP"):
            raise ToolError("Channel must be EMAIL, SMS, or WHATSAPP.")

    # Validate message_type if provided
    if message_type:
        message_type = message_type.upper()
        if message_type not in ("MESSAGE", "ALERT"):
            raise ToolError("Message type must be MESSAGE or ALERT.")

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
                    "/message/{message_id}",
                    path_params={"message_id": message_id},
                    resource_type="message",
                    resource_id=message_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Message '{message_id}' not found. "
                    "Use 'message_list' to see available messages."
                )

            # Merge with current state - PUT /message requires full object
            prev = previous_state
            payload: dict[str, Any] = {
                "id": message_id,
                "name": name.strip() if name else prev.get("name"),
                "subject": subject if subject is not None else prev.get("subject"),
                "content": content if content is not None else prev.get("content"),
                "channel": channel if channel else prev.get("channel"),
                "messageType": (
                    message_type if message_type else prev.get("messageType")
                ),
                "code": code if code is not None else prev.get("code"),
            }
            # Preserve linked data
            if previous_state.get("roleRegistrations"):
                payload["roleRegistrations"] = previous_state["roleRegistrations"]
            if previous_state.get("messageRoleStatuses"):
                payload["messageRoleStatuses"] = previous_state["messageRoleStatuses"]
            if previous_state.get("messageBots"):
                payload["messageBots"] = previous_state["messageBots"]
            if previous_state.get("businessKey"):
                payload["businessKey"] = previous_state["businessKey"]

            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="message",
                object_id=message_id,
                params={"changes": payload},
            )

            # Save rollback state
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="message",
                object_id=message_id,
                previous_state=previous_state,
            )

            try:
                message_data = await client.put(
                    "/message",
                    json=payload,
                    resource_type="message",
                    resource_id=message_id,
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={
                        "id": message_data.get("id"),
                        "name": message_data.get("name"),
                    },
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(
                    e, resource_type="message", resource_id=message_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="message", resource_id=message_id)

    result = _transform_message_response(message_data)
    result["previous_state"] = _transform_message_response(previous_state)
    result["audit_id"] = audit_id
    return result


async def message_delete(message_id: str) -> dict[str, Any]:
    """Delete a BPA message. Audited write operation.

    Args:
        message_id: Message ID to delete.

    Returns:
        dict with deleted (bool), message_id, deleted_message, audit_id.
    """
    if not message_id:
        raise ToolError(
            "Cannot delete message: 'message_id' is required. "
            "Use 'message_list' to find valid IDs."
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
                    "/message/{message_id}",
                    path_params={"message_id": message_id},
                    resource_type="message",
                    resource_id=message_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Message '{message_id}' not found. "
                    "Use 'message_list' to see available messages."
                )

            # Create PENDING audit record
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="message",
                object_id=message_id,
                params={},
            )

            # Save rollback state
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="message",
                object_id=message_id,
                previous_state=previous_state,
            )

            try:
                await client.delete(
                    "/message/{message_id}",
                    path_params={"message_id": message_id},
                    resource_type="message",
                    resource_id=message_id,
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={"deleted": True, "message_id": message_id},
                )

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(
                    e, resource_type="message", resource_id=message_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="message", resource_id=message_id)

    return {
        "deleted": True,
        "message_id": message_id,
        "deleted_message": _transform_message_response(previous_state),
        "audit_id": audit_id,
    }


def register_message_tools(mcp: Any) -> None:
    """Register message tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(message_list)
    mcp.tool()(message_get)
    mcp.tool()(message_create)
    mcp.tool()(message_update)
    mcp.tool()(message_delete)

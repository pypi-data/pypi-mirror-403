"""MCP tools for BPA notification operations.

This module provides tools for listing and creating BPA notifications
(email/SMS alerts configured for service events).
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
    "notification_list",
    "notification_create",
    "register_notification_tools",
]


def _transform_notification(notification: dict[str, Any]) -> dict[str, Any]:
    """Transform notification to snake_case format."""
    return {
        "id": notification.get("id"),
        "name": notification.get("name") or notification.get("title"),
        "type": notification.get("type") or notification.get("notificationType"),
        "trigger": notification.get("trigger") or notification.get("triggerEvent"),
        "enabled": notification.get("enabled", True),
        "template": notification.get("template") or notification.get("body"),
        "subject": notification.get("subject"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.notifications'",
        "find_by_type": "jq '.notifications[] | select(.type == \"email\")'",
        "find_by_trigger": "jq '.notifications[] | select(.trigger == \"on_submit\")'",
        "enabled_only": "jq '.notifications[] | select(.enabled == true)'",
    },
)
async def notification_list(
    service_id: str | int,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List notifications configured for a service.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        service_id: The service ID to list notifications for.
        limit: Maximum to return (default: 50).
        offset: Skip count (default: 0).

    Returns:
        dict with notifications, total, has_more, service_id.
    """
    # Normalize pagination parameters
    if limit <= 0:
        limit = 50
    if offset < 0:
        offset = 0

    try:
        async with BPAClient() as client:
            try:
                notifications_data = await client.get_list(
                    "/service/{service_id}/notifications",
                    path_params={"service_id": service_id},
                    resource_type="notification",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="notification")

    # Transform to consistent output format
    all_notifications = [_transform_notification(n) for n in notifications_data]

    # Sort by name for consistent ordering
    all_notifications.sort(key=lambda n: n.get("name") or "")

    # Calculate total before pagination
    total = len(all_notifications)

    # Apply pagination
    paginated = all_notifications[offset : offset + limit]

    # Calculate has_more
    has_more = (offset + limit) < total

    return {
        "notifications": paginated,
        "total": total,
        "has_more": has_more,
        "service_id": str(service_id),
    }


async def notification_create(
    service_id: str | int,
    name: str,
    notification_type: str,
    trigger: str,
    template: str | None = None,
    subject: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Create a notification for a service. Audited write operation.

    Args:
        service_id: The service ID to create the notification for.
        name: The notification name.
        notification_type: Type of notification (email, sms).
        trigger: Event that triggers the notification (on_submit, on_approve, etc.).
        template: The notification body template (default: None).
        subject: The email subject (default: None).
        enabled: Whether the notification is enabled (default: True).

    Returns:
        dict with id, name, type, trigger, enabled, audit_id.
    """
    # Pre-flight validation
    if not name or not name.strip():
        raise ToolError("Notification name is required.")
    if not notification_type or not notification_type.strip():
        raise ToolError("Notification type is required (e.g., 'email', 'sms').")
    if not trigger or not trigger.strip():
        raise ToolError(
            "Notification trigger is required (e.g., 'on_submit', 'on_approve')."
        )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    # Build payload
    payload: dict[str, Any] = {
        "name": name.strip(),
        "type": notification_type.strip(),
        "trigger": trigger.strip(),
        "enabled": enabled,
    }
    if template:
        payload["template"] = template
    if subject:
        payload["subject"] = subject

    try:
        async with BPAClient() as client:
            # Create audit record BEFORE API call
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="notification",
                params={"service_id": str(service_id), **payload},
            )

            try:
                notification_data = await client.post(
                    "/service/{service_id}/notification",
                    path_params={"service_id": service_id},
                    json=payload,
                    resource_type="notification",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = notification_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="notification",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "service_id": str(service_id),
                        "name": notification_data.get("name"),
                        "_operation": "create",
                    },
                )

                await audit_logger.mark_success(
                    audit_id=audit_id,
                    result={"id": created_id, "name": notification_data.get("name")},
                )

            except BPANotFoundError:
                await audit_logger.mark_failed(
                    audit_id=audit_id,
                    error_message=f"Service '{service_id}' not found",
                )
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
                raise translate_error(e, resource_type="notification")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="notification")

    # Transform response
    result = _transform_notification(notification_data)
    result["audit_id"] = audit_id
    result["service_id"] = str(service_id)

    return result


def register_notification_tools(mcp: Any) -> None:
    """Register notification tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(notification_list)
    mcp.tool()(notification_create)

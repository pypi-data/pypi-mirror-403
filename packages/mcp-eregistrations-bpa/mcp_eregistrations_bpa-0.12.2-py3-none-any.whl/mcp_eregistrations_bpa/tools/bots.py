"""MCP tools for BPA bot operations.

This module provides tools for listing, retrieving, creating, and updating BPA bots.
Bots are workflow automation entities that execute actions on form components.

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service/{service_id}/bot - List bots for a service
- GET /bot/{bot_id} - Get bot by ID
- POST /service/{service_id}/bot - Create bot within service
- PUT /bot - Update bot
"""

from __future__ import annotations

import re
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
    "bot_list",
    "bot_get",
    "bot_create",
    "bot_update",
    "bot_delete",
    "bot_validate",
    "bot_upgrade_version",
    "register_bot_tools",
]


def _transform_bot_response(data: dict[str, Any]) -> dict[str, Any]:
    """Transform bot API response from camelCase to snake_case.

    Args:
        data: Raw API response with camelCase keys.

    Returns:
        dict: Transformed response with snake_case keys.
    """
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "bot_type": data.get("botType"),
        "description": data.get("description"),
        "enabled": data.get("enabled", True),
        "service_id": data.get("serviceId"),
        "bot_service_id": data.get("botServiceId"),
        "short_name": data.get("shortName"),
        "category": data.get("category"),
    }


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.bots'",
        "find_by_type": "jq '.bots[] | select(.bot_type == \"BotType\")'",
        "find_by_name": "jq '.bots[] | select(.name | contains(\"search\"))'",
        "enabled_only": "jq '.bots[] | select(.enabled == true)'",
    },
)
async def bot_list(service_id: str | int) -> dict[str, Any]:
    """List bots for a service.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        service_id: Service ID to list bots for.

    Returns:
        dict with bots, service_id, total.
    """
    if not service_id:
        raise ToolError(
            "Cannot list bots: 'service_id' is required. "
            "Use 'service_list' to find valid service IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                bots_data = await client.get_list(
                    "/service/{service_id}/bot",
                    path_params={"service_id": service_id},
                    resource_type="bot",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot")

    # Transform to consistent output format
    bots = [_transform_bot_response(bot) for bot in bots_data]

    return {
        "bots": bots,
        "service_id": service_id,
        "total": len(bots),
    }


async def bot_get(bot_id: str | int) -> dict[str, Any]:
    """Get bot details by ID.

    Args:
        bot_id: Bot ID.

    Returns:
        dict with id, name, bot_type, description, enabled, service_id,
        bot_service_id, short_name, category.
    """
    if not bot_id:
        raise ToolError(
            "Cannot get bot: 'bot_id' is required. "
            "Use 'bot_list' with service_id to find valid bot IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                bot_data = await client.get(
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)

    return _transform_bot_response(bot_data)


def _validate_bot_create_params(
    service_id: str | int,
    bot_type: str,
    name: str,
    description: str | None,
) -> dict[str, Any]:
    """Validate bot_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        bot_type: Bot type identifier (required).
        name: Bot name (required).
        description: Bot description (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not bot_type or not str(bot_type).strip():
        errors.append("'bot_type' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot create bot: {error_msg}. Check required fields.")

    params: dict[str, Any] = {
        "botType": str(bot_type).strip(),
        "name": name.strip(),
        "enabled": True,
    }
    if description:
        params["description"] = description.strip()

    return params


async def bot_create(
    service_id: str | int,
    bot_type: str,
    name: str,
    description: str | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Create bot in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        bot_type: Bot type identifier.
        name: Bot name.
        description: Optional description.
        enabled: Enabled status (default: True).

    Returns:
        dict with id, name, bot_type, description, enabled, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_bot_create_params(
        service_id, bot_type, name, description
    )
    validated_params["enabled"] = enabled

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
                    f"Cannot create bot: Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="bot",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                bot_data = await client.post(
                    "/service/{service_id}/bot",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="bot",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = bot_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="bot",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": bot_data.get("name"),
                        "botType": bot_data.get("botType"),
                        "description": bot_data.get("description"),
                        "enabled": bot_data.get("enabled"),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "bot_id": bot_data.get("id"),
                        "name": bot_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                result = _transform_bot_response(bot_data)
                result["service_id"] = service_id  # Ensure service_id is always set
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="bot")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def _validate_bot_update_params(
    bot_id: str | int,
    name: str | None,
    description: str | None,
    enabled: bool | None,
    bot_service_id: str | None = None,
) -> dict[str, Any]:
    """Validate bot_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        bot_id: ID of bot to update (required).
        name: New name (optional).
        description: New description (optional).
        enabled: New enabled status (optional).
        bot_service_id: New external service reference (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not bot_id:
        errors.append("'bot_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    # At least one field must be provided for update
    if (
        name is None
        and description is None
        and enabled is None
        and bot_service_id is None
    ):
        errors.append(
            "At least one field (name, description, enabled, bot_service_id) "
            "must be provided"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(f"Cannot update bot: {error_msg}. Check required fields.")

    params: dict[str, Any] = {"id": bot_id}
    if name is not None:
        params["name"] = name.strip()
    if description is not None:
        params["description"] = description.strip()
    if enabled is not None:
        params["enabled"] = enabled
    if bot_service_id is not None:
        params["botServiceId"] = bot_service_id.strip()

    return params


async def bot_update(
    bot_id: str | int,
    name: str | None = None,
    description: str | None = None,
    enabled: bool | None = None,
    bot_service_id: str | None = None,
) -> dict[str, Any]:
    """Update a bot. Audited write operation.

    Args:
        bot_id: Bot ID to update.
        name: New name (optional).
        description: New description (optional).
        enabled: New enabled status (optional).
        bot_service_id: External service reference (optional, e.g., GDB service ID).

    Returns:
        dict with id, name, bot_type, description, enabled, previous_state, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_bot_update_params(
        bot_id, name, description, enabled, bot_service_id
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
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )

            # Merge provided changes with current state for full object PUT
            full_params = {
                "id": bot_id,
                "name": validated_params.get("name", previous_state.get("name")),
                "botType": previous_state.get("botType"),
                "description": validated_params.get(
                    "description", previous_state.get("description")
                ),
                "enabled": validated_params.get(
                    "enabled", previous_state.get("enabled", True)
                ),
                "serviceId": previous_state.get("serviceId"),
                "botServiceId": validated_params.get(
                    "botServiceId", previous_state.get("botServiceId")
                ),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="bot",
                object_id=str(bot_id),
                params={
                    "changes": validated_params,
                },
            )

            # Save rollback state for undo capability
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="bot",
                object_id=str(bot_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "botType": previous_state.get("botType"),
                    "description": previous_state.get("description"),
                    "enabled": previous_state.get("enabled"),
                    "serviceId": previous_state.get("serviceId"),
                    "botServiceId": previous_state.get("botServiceId"),
                },
            )

            try:
                bot_data = await client.put(
                    "/bot",
                    json=full_params,
                    resource_type="bot",
                    resource_id=bot_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "bot_id": bot_data.get("id"),
                        "name": bot_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                result = _transform_bot_response(bot_data)
                result["previous_state"] = {
                    "name": previous_state.get("name"),
                    "description": previous_state.get("description"),
                    "enabled": previous_state.get("enabled"),
                    "bot_service_id": previous_state.get("botServiceId"),
                }
                result["audit_id"] = audit_id
                return result

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="bot", resource_id=bot_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)


# =============================================================================
# bot_delete
# =============================================================================


def _validate_bot_delete_params(bot_id: str | int) -> None:
    """Validate bot_delete parameters before processing.

    Args:
        bot_id: ID of the bot to delete.

    Raises:
        ToolError: If validation fails.
    """
    if not bot_id or (isinstance(bot_id, str) and not bot_id.strip()):
        raise ToolError(
            "'bot_id' is required. "
            "Use 'bot_list' with service_id to see available bots."
        )


async def bot_delete(bot_id: str | int) -> dict[str, Any]:
    """Delete a bot. Audited write operation.

    Args:
        bot_id: Bot ID to delete.

    Returns:
        dict with deleted (bool), bot_id, deleted_bot, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_bot_delete_params(bot_id)

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
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="bot",
                object_id=str(bot_id),
                params={},
            )

            # Save rollback state for undo capability (recreate on rollback)
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="bot",
                object_id=str(bot_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "botType": previous_state.get("botType"),
                    "description": previous_state.get("description"),
                    "enabled": previous_state.get("enabled"),
                    "serviceId": previous_state.get("serviceId"),
                    "botServiceId": previous_state.get("botServiceId"),
                },
            )

            try:
                await client.delete(
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "bot_id": str(bot_id),
                    },
                )

                return {
                    "deleted": True,
                    "bot_id": str(bot_id),
                    "deleted_bot": _transform_bot_response(previous_state),
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="bot", resource_id=bot_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)


# =============================================================================
# bot_validate and bot_upgrade_version
# =============================================================================


def _parse_bot_service_id(bot_service_id: str | None) -> dict[str, str] | None:
    """Parse GDB bot service ID format.

    Format: GDB.GDB-{name}({version})-{operation}
    Example: GDB.GDB-NIPC REGISTRY(2.9)-read

    Args:
        bot_service_id: Bot service ID to parse.

    Returns:
        dict with type, name, version, operation or None if not GDB format.
    """
    if not bot_service_id:
        return None

    # Pattern: GDB.GDB-{name}({version})-{operation}
    match = re.match(r"^(GDB)\.(GDB-[^(]+)\(([^)]+)\)-(\w+)$", bot_service_id)
    if match:
        return {
            "type": match.group(1),
            "name": match.group(2),
            "version": match.group(3),
            "operation": match.group(4),
        }
    return None


def _extract_version(version_str: str) -> tuple[int, ...]:
    """Extract version tuple for sorting.

    Args:
        version_str: Version string like "2.9" or "3.0".

    Returns:
        Tuple of version numbers for comparison. Returns (-1,) for
        non-numeric versions to sort them before numeric versions.
    """
    if not version_str:
        return (-1,)
    try:
        # Strip any non-numeric suffix (e.g., "2.9-beta" -> "2.9")
        clean_version = version_str.split("-")[0].split("_")[0]
        parts = clean_version.split(".")
        return tuple(int(p) for p in parts if p.isdigit())
    except (ValueError, AttributeError):
        # Non-numeric versions sort before numeric ones
        return (-1,)


async def _get_mule_services(client: BPAClient | None = None) -> list[dict[str, Any]]:
    """Fetch available external services from BPA.

    Args:
        client: Optional existing BPAClient to reuse connection.

    Returns:
        List of mule service definitions.

    Raises:
        ToolError: If fetching mule services fails.
    """

    async def _fetch(c: BPAClient) -> list[dict[str, Any]]:
        result = await c.get(
            "/mule/services",
            params={"withoutdata": "true"},
            resource_type="mule_service",
        )
        # Handle both list and dict responses
        if isinstance(result, list):
            return result
        services: list[dict[str, Any]] = result.get("services", result.get("data", []))
        return services

    try:
        if client:
            return await _fetch(client)
        async with BPAClient() as new_client:
            return await _fetch(new_client)
    except BPAClientError as e:
        raise ToolError(
            f"Failed to fetch available GDB services: {e}. "
            "Check if mule services endpoint is accessible."
        )


async def bot_validate(bot_id: str | int) -> dict[str, Any]:
    """Validate bot configuration and external service availability.

    Checks if bot's external service (GDB) exists and if newer versions available.

    Args:
        bot_id: Bot ID to validate.

    Returns:
        dict with valid, bot_service_id, service_exists, current_version,
        available_versions, latest_version, needs_upgrade.
    """
    if not bot_id:
        raise ToolError(
            "Cannot validate bot: 'bot_id' is required. "
            "Use 'bot_list' with service_id to find valid bot IDs."
        )

    try:
        async with BPAClient() as client:
            # Get bot details
            try:
                bot_data = await client.get(
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )

            bot_service_id = bot_data.get("botServiceId")
            parsed = _parse_bot_service_id(bot_service_id)

            # If not a GDB bot, return basic validation
            if not parsed:
                return {
                    "valid": True,
                    "bot_id": str(bot_id),
                    "bot_name": bot_data.get("name"),
                    "bot_service_id": bot_service_id,
                    "is_gdb_bot": False,
                    "service_exists": None,
                    "message": "Bot does not use GDB external service. "
                    "No upgrade available.",
                }

            # Fetch available mule services (reuse connection)
            mule_services = await _get_mule_services(client)

            # Check if current service exists
            service_exists = any(s.get("id") == bot_service_id for s in mule_services)

            # Find all versions for this GDB service
            gdb_name = parsed["name"]
            operation = parsed["operation"]
            pattern = re.compile(
                rf"^GDB\.{re.escape(gdb_name)}\(([^)]+)\)-{re.escape(operation)}$"
            )

            available_versions: list[str] = []
            for svc in mule_services:
                svc_id = svc.get("id", "")
                match = pattern.match(svc_id)
                if match:
                    available_versions.append(match.group(1))

            # Sort versions
            available_versions.sort(key=_extract_version)
            latest_version = available_versions[-1] if available_versions else None
            current_version = parsed["version"]
            needs_upgrade = (
                latest_version is not None
                and latest_version != current_version
                and _extract_version(latest_version) > _extract_version(current_version)
            )

            return {
                "valid": service_exists,
                "bot_id": str(bot_id),
                "bot_name": bot_data.get("name"),
                "bot_service_id": bot_service_id,
                "is_gdb_bot": True,
                "service_exists": service_exists,
                "gdb_name": gdb_name,
                "operation": operation,
                "current_version": current_version,
                "available_versions": available_versions,
                "latest_version": latest_version,
                "needs_upgrade": needs_upgrade,
                "message": (
                    f"Upgrade available: {current_version} -> {latest_version}"
                    if needs_upgrade
                    else (
                        "Service not found in available mule services"
                        if not service_exists
                        else "Bot is up to date"
                    )
                ),
            }

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)


async def bot_upgrade_version(
    bot_id: str | int,
    target_version: str | None = None,
) -> dict[str, Any]:
    """Upgrade bot to newer GDB API version. Audited write operation.

    Args:
        bot_id: Bot to upgrade.
        target_version: Target version (default: latest available).

    Returns:
        dict with upgraded, old_version, new_version, old_bot_service_id,
        new_bot_service_id, audit_id.
    """
    if not bot_id:
        raise ToolError(
            "Cannot upgrade bot: 'bot_id' is required. "
            "Use 'bot_list' with service_id to find valid bot IDs."
        )

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    try:
        async with BPAClient() as client:
            # Get bot details
            try:
                bot_data = await client.get(
                    "/bot/{bot_id}",
                    path_params={"bot_id": bot_id},
                    resource_type="bot",
                    resource_id=bot_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Bot '{bot_id}' not found. "
                    "Use 'bot_list' with service_id to see available bots."
                )

            bot_service_id = bot_data.get("botServiceId")
            parsed = _parse_bot_service_id(bot_service_id)

            if not parsed:
                raise ToolError(
                    f"Bot '{bot_id}' does not use GDB external service. "
                    "Only GDB bots can be upgraded. "
                    f"Current bot_service_id: {bot_service_id}"
                )

            # Fetch available mule services (reuse connection)
            mule_services = await _get_mule_services(client)

            # Find all versions for this GDB service
            gdb_name = parsed["name"]
            operation = parsed["operation"]
            current_version = parsed["version"]
            pattern = re.compile(
                rf"^GDB\.{re.escape(gdb_name)}\(([^)]+)\)-{re.escape(operation)}$"
            )

            available_versions: list[str] = []
            version_to_service_id: dict[str, str] = {}
            for svc in mule_services:
                svc_id = svc.get("id", "")
                match = pattern.match(svc_id)
                if match:
                    ver = match.group(1)
                    available_versions.append(ver)
                    version_to_service_id[ver] = svc_id

            if not available_versions:
                raise ToolError(
                    f"No GDB services found for '{gdb_name}'. "
                    "Use 'muleservice_list' to see available services."
                )

            # Determine target version
            available_versions.sort(key=_extract_version)
            if target_version:
                if target_version not in version_to_service_id:
                    raise ToolError(
                        f"Target version '{target_version}' not available. "
                        f"Available versions: {', '.join(available_versions)}"
                    )
            else:
                target_version = available_versions[-1]

            # Check if upgrade is needed
            if target_version == current_version:
                return {
                    "upgraded": False,
                    "bot_id": str(bot_id),
                    "bot_name": bot_data.get("name"),
                    "old_version": current_version,
                    "new_version": current_version,
                    "message": "Bot is already at the target version.",
                }

            new_bot_service_id = version_to_service_id[target_version]

            # Create audit record BEFORE API call
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="upgrade",
                object_type="bot",
                object_id=str(bot_id),
                params={
                    "old_version": current_version,
                    "new_version": target_version,
                    "old_bot_service_id": bot_service_id,
                    "new_bot_service_id": new_bot_service_id,
                },
            )

            # Save rollback state
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="bot",
                object_id=str(bot_id),
                previous_state={
                    "id": bot_data.get("id"),
                    "name": bot_data.get("name"),
                    "botType": bot_data.get("botType"),
                    "description": bot_data.get("description"),
                    "enabled": bot_data.get("enabled"),
                    "serviceId": bot_data.get("serviceId"),
                    "botServiceId": bot_service_id,
                },
            )

            try:
                # Update bot with new service ID
                full_params = {
                    "id": bot_id,
                    "name": bot_data.get("name"),
                    "botType": bot_data.get("botType"),
                    "description": bot_data.get("description"),
                    "enabled": bot_data.get("enabled", True),
                    "serviceId": bot_data.get("serviceId"),
                    "botServiceId": new_bot_service_id,
                }

                updated_bot = await client.put(
                    "/bot",
                    json=full_params,
                    resource_type="bot",
                    resource_id=bot_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "bot_id": str(bot_id),
                        "old_version": current_version,
                        "new_version": target_version,
                        "old_bot_service_id": bot_service_id,
                        "new_bot_service_id": new_bot_service_id,
                    },
                )

                # Check if this is a downgrade
                is_downgrade = _extract_version(target_version) < _extract_version(
                    current_version
                )
                action_word = "downgraded" if is_downgrade else "upgraded"

                result = {
                    "upgraded": True,
                    "bot_id": str(bot_id),
                    "bot_name": updated_bot.get("name"),
                    "old_version": current_version,
                    "new_version": target_version,
                    "old_bot_service_id": bot_service_id,
                    "new_bot_service_id": new_bot_service_id,
                    "audit_id": audit_id,
                    "message": f"Successfully {action_word} from {current_version} "
                    f"to {target_version}",
                }
                if is_downgrade:
                    result["warning"] = (
                        "Version was downgraded, not upgraded. "
                        "Ensure this is intentional."
                    )
                return result

            except BPAClientError as e:
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="bot", resource_id=bot_id)

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="bot", resource_id=bot_id)


def register_bot_tools(mcp: Any) -> None:
    """Register bot tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(bot_list)
    mcp.tool()(bot_get)
    mcp.tool()(bot_validate)
    # Write operations (audit-before-write pattern)
    mcp.tool()(bot_create)
    mcp.tool()(bot_update)
    mcp.tool()(bot_delete)
    mcp.tool()(bot_upgrade_version)

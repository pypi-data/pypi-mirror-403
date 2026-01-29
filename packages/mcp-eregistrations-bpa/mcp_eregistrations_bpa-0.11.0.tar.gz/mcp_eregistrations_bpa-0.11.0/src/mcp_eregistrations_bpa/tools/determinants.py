"""MCP tools for BPA determinant operations.

This module provides tools for listing, retrieving, creating, and updating
BPA determinants. Determinants are accessed through service endpoints
(service-centric API design).

Write operations follow the audit-before-write pattern:
1. Validate parameters (pre-flight, no audit record if validation fails)
2. Create PENDING audit record
3. Execute BPA API call
4. Update audit record to SUCCESS or FAILED

API Endpoints used:
- GET /service/{service_id}/determinant - List determinants for service
- GET /determinant/{id} - Get determinant by ID
- POST /service/{service_id}/textdeterminant - Create text determinant
- PUT /service/{service_id}/textdeterminant - Update text determinant
- POST /service/{service_id}/selectdeterminant - Create select determinant
- POST /service/{service_id}/numericdeterminant - Create numeric determinant
- POST /service/{service_id}/booleandeterminant - Create boolean determinant
- POST /service/{service_id}/datedeterminant - Create date determinant
- POST /service/{service_id}/classificationdeterminant - Create classification det.
- DELETE /service/{service_id}/determinant/{determinant_id} - Delete determinant
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

# Operator normalization mapping (Story 10-4)
# Maps common operator variants to canonical BPA API format
_OPERATOR_ALIASES: dict[str, str] = {
    # Equals variants
    "equals": "EQUAL",
    "eq": "EQUAL",
    "==": "EQUAL",
    # Not equals variants
    "notequals": "NOT_EQUAL",
    "noteq": "NOT_EQUAL",
    "ne": "NOT_EQUAL",
    "!=": "NOT_EQUAL",
    "not_equals": "NOT_EQUAL",
    # Contains variants
    "contains": "CONTAINS",
    # Starts with variants
    "startswith": "STARTS_WITH",
    "starts_with": "STARTS_WITH",
    # Ends with variants
    "endswith": "ENDS_WITH",
    "ends_with": "ENDS_WITH",
    # Greater than variants
    "greaterthan": "GREATER_THAN",
    "greater_than": "GREATER_THAN",
    "gt": "GREATER_THAN",
    ">": "GREATER_THAN",
    # Less than variants
    "lessthan": "LESS_THAN",
    "less_than": "LESS_THAN",
    "lt": "LESS_THAN",
    "<": "LESS_THAN",
    # Greater than or equal variants
    "greaterthanorequal": "GREATER_THAN_OR_EQUAL",
    "greater_than_or_equal": "GREATER_THAN_OR_EQUAL",
    "gte": "GREATER_THAN_OR_EQUAL",
    "ge": "GREATER_THAN_OR_EQUAL",
    ">=": "GREATER_THAN_OR_EQUAL",
    # Less than or equal variants
    "lessthanorequal": "LESS_THAN_OR_EQUAL",
    "less_than_or_equal": "LESS_THAN_OR_EQUAL",
    "lte": "LESS_THAN_OR_EQUAL",
    "le": "LESS_THAN_OR_EQUAL",
    "<=": "LESS_THAN_OR_EQUAL",
}


def _normalize_operator(operator: str) -> str:
    """Normalize operator to canonical BPA API format.

    Accepts various formats (camelCase, lowercase, symbols) and converts
    to the uppercase underscore format expected by BPA API.

    Args:
        operator: Operator in any supported format.

    Returns:
        Normalized operator string (e.g., "EQUAL", "NOT_EQUAL", "GREATER_THAN").

    Examples:
        >>> _normalize_operator("equals")
        "EQUAL"
        >>> _normalize_operator("notEquals")
        "NOT_EQUAL"
        >>> _normalize_operator(">=")
        "GREATER_THAN_OR_EQUAL"
    """
    cleaned = operator.strip().lower()

    # Check alias mapping first
    if cleaned in _OPERATOR_ALIASES:
        return _OPERATOR_ALIASES[cleaned]

    # If already in canonical format, just uppercase
    return operator.strip().upper()


__all__ = [
    "determinant_list",
    "determinant_get",
    "determinant_search",
    "determinant_delete",
    "textdeterminant_create",
    "textdeterminant_update",
    "selectdeterminant_create",
    "numericdeterminant_create",
    "booleandeterminant_create",
    "datedeterminant_create",
    "classificationdeterminant_create",
    "griddeterminant_create",
    "register_determinant_tools",
]


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.determinants'",
        "by_type": "jq '.determinants[] | select(.type == \"text\")'",
        "by_field": "jq '.determinants[] | select(.target_form_field_key==\"x\")'",
        "by_name": "jq '.determinants[] | select(.name | contains(\"x\"))'",
    },
)
async def determinant_list(service_id: str | int) -> dict[str, Any]:
    """List determinants for a service.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        service_id: Service ID to list determinants for.

    Returns:
        dict with determinants, total, service_id.
    """
    try:
        async with BPAClient() as client:
            determinants_data = await client.get_list(
                "/service/{service_id}/determinant",
                path_params={"service_id": service_id},
                resource_type="determinant",
            )
    except BPAClientError as e:
        raise translate_error(e, resource_type="determinant")

    # Transform to consistent output format with snake_case keys
    determinants = []
    for det in determinants_data:
        determinant_item: dict[str, Any] = {
            "id": det.get("id"),
            "name": det.get("name"),
            "type": det.get("type"),
            "operator": det.get("operator"),
            "target_form_field_key": det.get("targetFormFieldKey"),
            "condition_summary": det.get("conditionSummary"),
            "json_condition": det.get("jsonCondition"),
        }
        # Include type-specific value fields if present
        if det.get("textValue") is not None:
            determinant_item["text_value"] = det.get("textValue")
        if det.get("selectValue") is not None:
            determinant_item["select_value"] = det.get("selectValue")
        if det.get("numericValue") is not None:
            determinant_item["numeric_value"] = det.get("numericValue")
        if det.get("booleanValue") is not None:
            determinant_item["boolean_value"] = det.get("booleanValue")
        if det.get("dateValue") is not None:
            determinant_item["date_value"] = det.get("dateValue")
        if det.get("isCurrentDate") is not None:
            determinant_item["is_current_date"] = det.get("isCurrentDate")
        determinants.append(determinant_item)

    return {
        "determinants": determinants,
        "total": len(determinants),
        "service_id": service_id,
    }


async def determinant_get(determinant_id: str | int) -> dict[str, Any]:
    """Get determinant details by ID.

    Args:
        determinant_id: Determinant ID.

    Returns:
        dict with id, name, type, service_id (if available), condition_logic,
        json_condition.
    """
    try:
        async with BPAClient() as client:
            try:
                determinant_data = await client.get(
                    "/determinant/{id}",
                    path_params={"id": determinant_id},
                    resource_type="determinant",
                    resource_id=determinant_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Determinant '{determinant_id}' not found. "
                    "Use 'determinant_list' with service_id to see determinants."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="determinant", resource_id=determinant_id
        )

    # Build response with all condition-related fields
    result: dict[str, Any] = {
        "id": determinant_data.get("id"),
        "name": determinant_data.get("name"),
        "type": determinant_data.get("type"),
        "operator": determinant_data.get("operator"),
        "target_form_field_key": determinant_data.get("targetFormFieldKey"),
        "condition_logic": determinant_data.get("conditionLogic"),
        "json_condition": determinant_data.get("jsonCondition"),
        "condition_summary": determinant_data.get("conditionSummary"),
    }

    # Include service_id if present in API response (Story 10-7: NFR4 complete context)
    if determinant_data.get("serviceId") is not None:
        result["service_id"] = determinant_data.get("serviceId")

    # Include type-specific value fields if present
    if determinant_data.get("textValue") is not None:
        result["text_value"] = determinant_data.get("textValue")
    if determinant_data.get("selectValue") is not None:
        result["select_value"] = determinant_data.get("selectValue")
    if determinant_data.get("numericValue") is not None:
        result["numeric_value"] = determinant_data.get("numericValue")
    if determinant_data.get("booleanValue") is not None:
        result["boolean_value"] = determinant_data.get("booleanValue")
    if determinant_data.get("dateValue") is not None:
        result["date_value"] = determinant_data.get("dateValue")
    if determinant_data.get("isCurrentDate") is not None:
        result["is_current_date"] = determinant_data.get("isCurrentDate")

    return result


def _validate_textdeterminant_create_params(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    text_value: str = "",
) -> dict[str, Any]:
    """Validate textdeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        operator: Comparison operator (required). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (required).
        text_value: The text value to compare against (default: "" for isEmpty checks).

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

    if not operator or not operator.strip():
        errors.append("'operator' is required")

    valid_operators = [
        "EQUAL",
        "NOT_EQUAL",
        "CONTAINS",
        "STARTS_WITH",
        "ENDS_WITH",
    ]
    # Normalize operator to canonical format (Story 10-4)
    normalized_operator = _normalize_operator(operator) if operator else ""
    if operator and normalized_operator not in valid_operators:
        errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create text determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'operator', and "
            "'target_form_field_key' parameters."
        )

    return {
        "name": name.strip(),
        "operator": normalized_operator,
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "text",
        "textValue": text_value.strip() if text_value else "",
        "determinantInsideGrid": False,
    }


def _validate_textdeterminant_update_params(
    service_id: str | int,
    determinant_id: str | int,
    name: str | None,
    operator: str | None,
    target_form_field_key: str | None,
    condition_logic: str | None,
    json_condition: str | None,
) -> dict[str, Any]:
    """Validate textdeterminant_update parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.

    Args:
        service_id: Parent service ID (required).
        determinant_id: Determinant ID to update (required).
        name: New name (optional).
        operator: Comparison operator (optional). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (optional).
        condition_logic: New condition logic (optional).
        json_condition: New JSON condition (optional).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not determinant_id:
        errors.append("'determinant_id' is required")

    if name is not None and not name.strip():
        errors.append("'name' cannot be empty when provided")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    valid_operators = [
        "EQUAL",
        "NOT_EQUAL",
        "CONTAINS",
        "STARTS_WITH",
        "ENDS_WITH",
    ]
    # Normalize operator to canonical format (Story 10-4)
    normalized_operator = _normalize_operator(operator) if operator else None
    if operator is not None:
        if not operator.strip():
            errors.append("'operator' cannot be empty when provided")
        elif normalized_operator not in valid_operators:
            errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if target_form_field_key is not None and not target_form_field_key.strip():
        errors.append("'target_form_field_key' cannot be empty when provided")

    # At least one field must be provided for update
    if all(
        v is None
        for v in [
            name,
            operator,
            target_form_field_key,
            condition_logic,
            json_condition,
        ]
    ):
        errors.append(
            "At least one field (name, operator, target_form_field_key, "
            "condition_logic, json_condition) required"
        )

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot update text determinant: {error_msg}. Check required fields."
        )

    params: dict[str, Any] = {"id": determinant_id}
    if name is not None:
        params["name"] = name.strip()
    if normalized_operator is not None:
        params["operator"] = normalized_operator
    if target_form_field_key is not None:
        params["targetFormFieldKey"] = target_form_field_key.strip()
    if condition_logic is not None:
        params["conditionLogic"] = condition_logic
    if json_condition is not None:
        params["jsonCondition"] = json_condition

    return params


def _validate_selectdeterminant_create_params(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    select_value: str,
) -> dict[str, Any]:
    """Validate selectdeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        operator: Comparison operator (required). Valid values: equals, notEquals,
            contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty.
        target_form_field_key: The form field key this determinant targets (required).
        select_value: The select option value this determinant matches (required).

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

    if not operator or not operator.strip():
        errors.append("'operator' is required")

    valid_operators = [
        "EQUAL",
        "NOT_EQUAL",
    ]
    # Normalize operator to canonical format (Story 10-4)
    normalized_operator = _normalize_operator(operator) if operator else ""
    if operator and normalized_operator not in valid_operators:
        errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if not select_value or not select_value.strip():
        errors.append("'select_value' is required")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create select determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'operator', "
            "'target_form_field_key', and 'select_value' parameters."
        )

    return {
        "name": name.strip(),
        "operator": normalized_operator,
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "radio",
        "selectValue": select_value.strip(),
        "determinantInsideGrid": False,
    }


async def textdeterminant_create(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    text_value: str = "",
    condition_logic: str | None = None,
    json_condition: str | None = None,
) -> dict[str, Any]:
    """Create text determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        operator: EQUAL, NOT_EQUAL, CONTAINS, STARTS_WITH, or ENDS_WITH.
        target_form_field_key: Form field key to evaluate.
        text_value: Value to compare (default: "" for isEmpty).
        condition_logic: Optional condition expression.
        json_condition: Optional JSON condition.

    Returns:
        dict with id, name, type, operator, target_form_field_key, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_textdeterminant_create_params(
        service_id, name, operator, target_form_field_key, text_value
    )

    # Add optional parameters
    if condition_logic is not None:
        validated_params["conditionLogic"] = condition_logic
    if json_condition is not None:
        validated_params["jsonCondition"] = json_condition

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
                    f"Cannot create text determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="textdeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/textdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="textdeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "operator": determinant_data.get("operator"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "textValue": determinant_data.get("textValue"),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "text",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "text_value": determinant_data.get("textValue"),
                    "condition_logic": determinant_data.get("conditionLogic"),
                    "json_condition": determinant_data.get("jsonCondition"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


async def textdeterminant_update(
    service_id: str | int,
    determinant_id: str | int,
    name: str | None = None,
    operator: str | None = None,
    target_form_field_key: str | None = None,
    condition_logic: str | None = None,
    json_condition: str | None = None,
) -> dict[str, Any]:
    """Update a text determinant. Audited write operation.

    Args:
        service_id: Parent service ID.
        determinant_id: Determinant ID to update.
        name: New name (optional).
        operator: New operator (optional).
        target_form_field_key: New field key (optional).
        condition_logic: New condition (optional).
        json_condition: New JSON condition (optional).

    Returns:
        dict with id, name, operator, target_form_field_key, previous_state, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_textdeterminant_update_params(
        service_id,
        determinant_id,
        name,
        operator,
        target_form_field_key,
        condition_logic,
        json_condition,
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
                    "/determinant/{id}",
                    path_params={"id": determinant_id},
                    resource_type="determinant",
                    resource_id=determinant_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Determinant '{determinant_id}' not found. "
                    "Use 'determinant_list' with service_id to see determinants."
                )

            # Normalize previous_state to snake_case for consistency
            normalized_previous_state = {
                "id": previous_state.get("id"),
                "name": previous_state.get("name"),
                "operator": previous_state.get("operator"),
                "target_form_field_key": previous_state.get("targetFormFieldKey"),
                "condition_logic": previous_state.get("conditionLogic"),
                "json_condition": previous_state.get("jsonCondition"),
            }

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="update",
                object_type="textdeterminant",
                object_id=str(determinant_id),
                params={
                    "service_id": str(service_id),
                    "changes": validated_params,
                },
            )

            # Save rollback state for undo capability
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="textdeterminant",
                object_id=str(determinant_id),
                previous_state={
                    "id": previous_state.get("id"),
                    "name": previous_state.get("name"),
                    "operator": previous_state.get("operator"),
                    "targetFormFieldKey": previous_state.get("targetFormFieldKey"),
                    "conditionLogic": previous_state.get("conditionLogic"),
                    "jsonCondition": previous_state.get("jsonCondition"),
                    "serviceId": service_id,
                },
            )

            try:
                determinant_data = await client.put(
                    "/service/{service_id}/textdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                    resource_id=determinant_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": determinant_data.get("id"),
                        "name": determinant_data.get("name"),
                        "changes_applied": {
                            k: v for k, v in validated_params.items() if k != "id"
                        },
                    },
                )

                return {
                    "id": determinant_data.get("id"),
                    "name": determinant_data.get("name"),
                    "type": "text",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "condition_logic": determinant_data.get("conditionLogic"),
                    "json_condition": determinant_data.get("jsonCondition"),
                    "service_id": service_id,
                    "previous_state": normalized_previous_state,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="determinant", resource_id=determinant_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="determinant", resource_id=determinant_id
        )


async def selectdeterminant_create(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    select_value: str,
    condition_logic: str | None = None,
    json_condition: str | None = None,
) -> dict[str, Any]:
    """Create select determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        operator: EQUAL or NOT_EQUAL.
        target_form_field_key: Form field key to evaluate.
        select_value: Option value to match.
        condition_logic: Optional condition expression.
        json_condition: Optional JSON condition.

    Returns:
        dict with id, name, type, operator, select_value, service_id, audit_id.
    """
    # Pre-flight validation
    validated_params = _validate_selectdeterminant_create_params(
        service_id, name, operator, target_form_field_key, select_value
    )

    # Add optional parameters
    if condition_logic is not None:
        validated_params["conditionLogic"] = condition_logic
    if json_condition is not None:
        validated_params["jsonCondition"] = json_condition

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
                    f"Cannot create select determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="selectdeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/selectdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="selectdeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "operator": determinant_data.get("operator"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "selectValue": determinant_data.get("selectValue"),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "radio",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "select_value": determinant_data.get("selectValue"),
                    "condition_logic": determinant_data.get("conditionLogic"),
                    "json_condition": determinant_data.get("jsonCondition"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


# =============================================================================
# numericdeterminant_create
# =============================================================================


def _validate_numericdeterminant_create_params(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    numeric_value: int | float,
) -> dict[str, Any]:
    """Validate numericdeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        operator: Comparison operator (required). Valid values: EQUAL, NOT_EQUAL,
            GREATER_THAN, LESS_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN_OR_EQUAL.
        target_form_field_key: The form field key this determinant targets (required).
        numeric_value: The numeric value to compare against (required).

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

    if not operator or not operator.strip():
        errors.append("'operator' is required")

    valid_operators = [
        "EQUAL",
        "NOT_EQUAL",
        "GREATER_THAN",
        "LESS_THAN",
        "GREATER_THAN_OR_EQUAL",
        "LESS_THAN_OR_EQUAL",
    ]
    # Normalize operator to canonical format (Story 10-4)
    normalized_operator = _normalize_operator(operator) if operator else ""
    if operator and normalized_operator not in valid_operators:
        errors.append(f"'operator' must be one of: {', '.join(valid_operators)}")

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if numeric_value is None:
        errors.append("'numeric_value' is required")
    elif not isinstance(numeric_value, int | float):
        errors.append("'numeric_value' must be a number (int or float)")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create numeric determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'operator', "
            "'target_form_field_key', and 'numeric_value' parameters."
        )

    return {
        "name": name.strip(),
        "operator": normalized_operator,
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "numeric",
        "numericValue": numeric_value,
        "determinantInsideGrid": False,
    }


async def numericdeterminant_create(
    service_id: str | int,
    name: str,
    operator: str,
    target_form_field_key: str,
    numeric_value: int | float,
) -> dict[str, Any]:
    """Create numeric determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        operator: EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN,
            GREATER_THAN_OR_EQUAL, or LESS_THAN_OR_EQUAL.
        target_form_field_key: Form field key to evaluate.
        numeric_value: Numeric value to compare against.

    Returns:
        dict with id, name, type, operator, numeric_value, target_form_field_key,
        service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_numericdeterminant_create_params(
        service_id, name, operator, target_form_field_key, numeric_value
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
                    f"Cannot create numeric determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="numericdeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/numericdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="numericdeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "operator": determinant_data.get("operator"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "numericValue": determinant_data.get("numericValue"),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "numeric",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "numeric_value": determinant_data.get("numericValue"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


# =============================================================================
# booleandeterminant_create
# =============================================================================


def _validate_booleandeterminant_create_params(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    boolean_value: bool,
) -> dict[str, Any]:
    """Validate booleandeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        target_form_field_key: The form field key this determinant targets (required).
        boolean_value: The boolean value to check (True/False) (required).

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

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if boolean_value is None:
        errors.append("'boolean_value' is required")
    elif not isinstance(boolean_value, bool):
        errors.append("'boolean_value' must be a boolean (True or False)")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create boolean determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'target_form_field_key', "
            "and 'boolean_value' parameters."
        )

    return {
        "name": name.strip(),
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "boolean",
        "booleanValue": boolean_value,
        "determinantInsideGrid": False,
    }


async def booleandeterminant_create(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    boolean_value: bool,
) -> dict[str, Any]:
    """Create boolean determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        target_form_field_key: Form field key to evaluate (checkbox field).
        boolean_value: Boolean value to check (True or False).

    Returns:
        dict with id, name, type, boolean_value, target_form_field_key,
        service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_booleandeterminant_create_params(
        service_id, name, target_form_field_key, boolean_value
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
                    f"Cannot create boolean determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="booleandeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/booleandeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="booleandeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "booleanValue": determinant_data.get("booleanValue"),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "boolean",
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "boolean_value": determinant_data.get("booleanValue"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


# =============================================================================
# datedeterminant_create
# =============================================================================

# Valid operators for date determinants
DATE_DETERMINANT_OPERATORS = frozenset(
    {
        "EQUAL",
        "NOT_EQUAL",
        "GREATER_THAN",
        "LESS_THAN",
        "GREATER_THAN_OR_EQUAL",
        "LESS_THAN_OR_EQUAL",
    }
)


def _validate_datedeterminant_create_params(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    operator: str,
    is_current_date: bool | None = None,
    date_value: str | None = None,
) -> dict[str, Any]:
    """Validate datedeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        target_form_field_key: Form field key to evaluate (required).
        operator: Comparison operator (required).
        is_current_date: Whether to compare against current date.
        date_value: Specific date to compare against (ISO 8601: YYYY-MM-DD).

    Returns:
        dict: Validated parameters ready for API call.

    Raises:
        ToolError: If validation fails.
    """
    import re

    errors = []

    if not service_id:
        errors.append("'service_id' is required")

    if not name or not name.strip():
        errors.append("'name' is required and cannot be empty")

    if name and len(name.strip()) > 255:
        errors.append("'name' must be 255 characters or less")

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if not operator or not operator.strip():
        errors.append("'operator' is required")
    # Normalize operator to canonical format (Story 10-4)
    normalized_operator = _normalize_operator(operator) if operator else ""
    if operator and normalized_operator not in DATE_DETERMINANT_OPERATORS:
        valid_ops = ", ".join(sorted(DATE_DETERMINANT_OPERATORS))
        errors.append(f"'operator' must be one of: {valid_ops}")

    # Must provide either is_current_date=True or a date_value
    if not is_current_date and not date_value:
        errors.append("Either 'is_current_date=True' or 'date_value' must be provided")

    # Validate date format if provided
    if date_value:
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(date_pattern, date_value.strip()):
            errors.append("'date_value' must be in ISO 8601 format (YYYY-MM-DD)")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create date determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'target_form_field_key', "
            "'operator', and either 'is_current_date=True' or 'date_value'."
        )

    # Build API payload
    payload: dict[str, Any] = {
        "name": name.strip(),
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "date",
        "operator": normalized_operator,
        "determinantInsideGrid": False,
    }

    if is_current_date:
        payload["isCurrentDate"] = True
    else:
        payload["isCurrentDate"] = False
        payload["dateValue"] = date_value.strip() if date_value else None

    return payload


async def datedeterminant_create(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    operator: str,
    is_current_date: bool | None = None,
    date_value: str | None = None,
) -> dict[str, Any]:
    """Create date determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        target_form_field_key: Form field key to evaluate (date field).
        operator: Comparison operator (EQUAL, NOT_EQUAL, GREATER_THAN,
            LESS_THAN, GREATER_THAN_OR_EQUAL, LESS_THAN_OR_EQUAL).
        is_current_date: Compare against today's date (default: None).
        date_value: Specific date to compare (ISO 8601: YYYY-MM-DD).

    Returns:
        dict with id, name, type, operator, target_form_field_key,
        is_current_date, date_value, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_datedeterminant_create_params(
        service_id, name, target_form_field_key, operator, is_current_date, date_value
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
                    f"Cannot create date determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="datedeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/datedeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="datedeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "operator": determinant_data.get("operator"),
                        "isCurrentDate": determinant_data.get("isCurrentDate"),
                        "dateValue": determinant_data.get("dateValue"),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "date",
                    "operator": determinant_data.get("operator"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "is_current_date": determinant_data.get("isCurrentDate"),
                    "date_value": determinant_data.get("dateValue"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


# =============================================================================
# classificationdeterminant_create
# =============================================================================

# Valid operators for classification determinants
CLASSIFICATION_DETERMINANT_OPERATORS = frozenset({"EQUAL", "NOT_EQUAL"})

# Valid subjects for classification determinants
CLASSIFICATION_DETERMINANT_SUBJECTS = frozenset({"ALL", "ANY", "NONE"})


def _validate_classificationdeterminant_create_params(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    classification_field: str,
    operator: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """Validate classificationdeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        target_form_field_key: Form field key to evaluate (required).
        classification_field: Catalog field ID (required).
        operator: Comparison operator (EQUAL, NOT_EQUAL) (required).
        subject: How to evaluate multi-select (ALL, ANY, NONE) (default: ALL).

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

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if not classification_field or not classification_field.strip():
        errors.append("'classification_field' is required")

    if not operator or not operator.strip():
        errors.append("'operator' is required")
    elif operator.strip().upper() not in CLASSIFICATION_DETERMINANT_OPERATORS:
        valid_ops = ", ".join(sorted(CLASSIFICATION_DETERMINANT_OPERATORS))
        errors.append(f"'operator' must be one of: {valid_ops}")

    # Default subject to ALL if not provided
    resolved_subject = subject.strip().upper() if subject else "ALL"
    if resolved_subject not in CLASSIFICATION_DETERMINANT_SUBJECTS:
        valid_subjects = ", ".join(sorted(CLASSIFICATION_DETERMINANT_SUBJECTS))
        errors.append(f"'subject' must be one of: {valid_subjects}")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create classification determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'target_form_field_key', "
            "'classification_field', 'operator', and optionally 'subject'."
        )

    return {
        "name": name.strip(),
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "classification",
        "operator": operator.strip().upper(),
        "subject": resolved_subject,
        "classificationField": classification_field.strip(),
        "determinantInsideGrid": False,
    }


async def classificationdeterminant_create(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    classification_field: str,
    operator: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """Create classification determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        target_form_field_key: Form field key to evaluate.
        classification_field: Catalog field ID (UUID).
        operator: Comparison operator (EQUAL, NOT_EQUAL).
        subject: How to evaluate multi-select (ALL, ANY, NONE; default: ALL).

    Returns:
        dict with id, name, type, operator, subject, target_form_field_key,
        classification_field, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_classificationdeterminant_create_params(
        service_id, name, target_form_field_key, classification_field, operator, subject
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
                    f"Cannot create classification determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="classificationdeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/classificationdeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="classificationdeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "operator": determinant_data.get("operator"),
                        "subject": determinant_data.get("subject"),
                        "classificationField": determinant_data.get(
                            "classificationField"
                        ),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "classification",
                    "operator": determinant_data.get("operator"),
                    "subject": determinant_data.get("subject"),
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "classification_field": determinant_data.get("classificationField"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


# =============================================================================
# griddeterminant_create
# =============================================================================


def _validate_griddeterminant_create_params(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    row_determinant_id: str,
) -> dict[str, Any]:
    """Validate griddeterminant_create parameters (pre-flight).

    Returns validated params dict or raises ToolError if invalid.
    No audit record is created for validation failures.

    Args:
        service_id: Parent service ID (required).
        name: Determinant name (required).
        target_form_field_key: Grid component key to evaluate (required).
        row_determinant_id: ID of the determinant that evaluates each row (required).

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

    if not target_form_field_key or not target_form_field_key.strip():
        errors.append("'target_form_field_key' is required")

    if not row_determinant_id or not row_determinant_id.strip():
        errors.append("'row_determinant_id' is required")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create grid determinant: {error_msg}. "
            "Provide valid 'service_id', 'name', 'target_form_field_key', "
            "and 'row_determinant_id' parameters."
        )

    return {
        "name": name.strip(),
        "targetFormFieldKey": target_form_field_key.strip(),
        "determinantType": "FORMFIELD",
        "type": "grid",
        "determinantInsideGrid": True,
        "rowDeterminantId": row_determinant_id.strip(),
    }


async def griddeterminant_create(
    service_id: str | int,
    name: str,
    target_form_field_key: str,
    row_determinant_id: str,
) -> dict[str, Any]:
    """Create grid determinant in a service. Audited write operation.

    Args:
        service_id: Parent service ID.
        name: Determinant name.
        target_form_field_key: Grid component key to evaluate.
        row_determinant_id: ID of the determinant evaluating each row.

    Returns:
        dict with id, name, type, target_form_field_key, determinant_inside_grid,
        row_determinant_id, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    validated_params = _validate_griddeterminant_create_params(
        service_id, name, target_form_field_key, row_determinant_id
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
                    f"Cannot create grid determinant: Service '{service_id}' "
                    "not found. Use 'service_list' to see available services."
                )

            # Verify row determinant exists before creating audit record
            try:
                await client.get(
                    "/determinant/{id}",
                    path_params={"id": row_determinant_id},
                    resource_type="determinant",
                    resource_id=row_determinant_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Cannot create grid determinant: Row determinant "
                    f"'{row_determinant_id}' not found. Create the row determinant "
                    "first using textdeterminant_create, selectdeterminant_create, "
                    "or similar tools."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="griddeterminant",
                params={
                    "service_id": str(service_id),
                    **validated_params,
                },
            )

            try:
                determinant_data = await client.post(
                    "/service/{service_id}/griddeterminant",
                    path_params={"service_id": service_id},
                    json=validated_params,
                    resource_type="determinant",
                )

                # Save rollback state (for create, save ID to enable deletion)
                created_id = determinant_data.get("id")
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="griddeterminant",
                    object_id=str(created_id),
                    previous_state={
                        "id": created_id,
                        "name": determinant_data.get("name"),
                        "targetFormFieldKey": determinant_data.get(
                            "targetFormFieldKey"
                        ),
                        "rowDeterminantId": determinant_data.get("rowDeterminantId"),
                        "determinantInsideGrid": determinant_data.get(
                            "determinantInsideGrid"
                        ),
                        "serviceId": str(service_id),
                        "_operation": "create",  # Marker for rollback to DELETE
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "determinant_id": created_id,
                        "name": determinant_data.get("name"),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "id": created_id,
                    "name": determinant_data.get("name"),
                    "type": "grid",
                    "target_form_field_key": determinant_data.get("targetFormFieldKey"),
                    "determinant_inside_grid": determinant_data.get(
                        "determinantInsideGrid"
                    ),
                    "row_determinant_id": determinant_data.get("rowDeterminantId"),
                    "service_id": service_id,
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="determinant")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


# =============================================================================
# determinant_delete
# =============================================================================


def _validate_determinant_delete_params(
    service_id: str | int, determinant_id: str | int
) -> None:
    """Validate determinant_delete parameters before processing.

    Args:
        service_id: ID of the service containing the determinant.
        determinant_id: ID of the determinant to delete.

    Raises:
        ToolError: If validation fails.
    """
    if not service_id or (isinstance(service_id, str) and not service_id.strip()):
        raise ToolError(
            "'service_id' is required. Use 'service_list' to see available services."
        )
    if not determinant_id or (
        isinstance(determinant_id, str) and not determinant_id.strip()
    ):
        raise ToolError(
            "'determinant_id' is required. "
            "Use 'determinant_list' with service_id to see available determinants."
        )


async def determinant_delete(
    service_id: str | int, determinant_id: str | int
) -> dict[str, Any]:
    """Delete a determinant. Audited write operation.

    Args:
        service_id: Service ID containing the determinant.
        determinant_id: Determinant ID to delete.

    Returns:
        dict with deleted (bool), determinant_id, service_id, deleted_determinant,
        audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_determinant_delete_params(service_id, determinant_id)

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
                    "/determinant/{determinant_id}",
                    path_params={"determinant_id": determinant_id},
                    resource_type="determinant",
                    resource_id=determinant_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Determinant '{determinant_id}' not found. "
                    "Use 'determinant_list' with service_id to see available "
                    "determinants."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="determinant",
                object_id=str(determinant_id),
                params={"service_id": str(service_id)},
            )

            # Save rollback state for undo capability (recreate on rollback)
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="determinant",
                object_id=str(determinant_id),
                previous_state=previous_state,  # Keep full state for recreation
            )

            try:
                await client.delete(
                    "/service/{service_id}/determinant/{determinant_id}",
                    path_params={
                        "service_id": service_id,
                        "determinant_id": determinant_id,
                    },
                    resource_type="determinant",
                    resource_id=determinant_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "determinant_id": str(determinant_id),
                        "service_id": str(service_id),
                    },
                )

                return {
                    "deleted": True,
                    "determinant_id": str(determinant_id),
                    "service_id": str(service_id),
                    "deleted_determinant": {
                        "id": previous_state.get("id"),
                        "name": previous_state.get("name"),
                        "type": previous_state.get("type"),
                        "operator": previous_state.get("operator"),
                        "target_form_field_key": previous_state.get(
                            "targetFormFieldKey"
                        ),
                    },
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="determinant", resource_id=determinant_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(
            e, resource_type="determinant", resource_id=determinant_id
        )


# =============================================================================
# determinant_search
# =============================================================================


async def determinant_search(
    service_id: str | int,
    name_pattern: str | None = None,
    determinant_type: str | None = None,
    operator: str | None = None,
    target_field_key: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search determinants by criteria to discover reusable conditions.

    This read-only tool helps find existing determinants before creating new ones,
    promoting reuse and consistency.

    Args:
        service_id: Service ID to search within.
        name_pattern: Substring to match in determinant names (case-insensitive).
        determinant_type: Filter by type (text, boolean, date, radio, numeric,
            classification, grid).
        operator: Filter by operator (e.g., EQUAL, NOT_EQUAL, GREATER_THAN).
        target_field_key: Filter by target form field key.
        limit: Maximum results to return (default: 20, max: 100).

    Returns:
        dict with determinants, total, returned, service_id, filters_applied.
    """
    import re

    # Validate limit
    if limit < 1:
        limit = 20
    elif limit > 100:
        limit = 100

    try:
        async with BPAClient() as client:
            # Fetch all determinants for the service
            determinants_data = await client.get_list(
                "/service/{service_id}/determinant",
                path_params={"service_id": service_id},
                resource_type="determinant",
            )
    except BPANotFoundError:
        raise ToolError(
            f"Service '{service_id}' not found. "
            "Use 'service_list' to see available services."
        )
    except BPAClientError as e:
        raise translate_error(e, resource_type="determinant")

    # Apply filters
    filtered_determinants = []
    for det in determinants_data:
        # Filter by name pattern (case-insensitive substring match)
        if name_pattern:
            det_name = det.get("name", "") or ""
            if not re.search(re.escape(name_pattern), det_name, re.IGNORECASE):
                continue

        # Filter by type
        if determinant_type:
            if det.get("type", "").lower() != determinant_type.lower():
                continue

        # Filter by operator
        if operator:
            det_operator = det.get("operator", "") or ""
            if det_operator.upper() != operator.upper():
                continue

        # Filter by target field key
        if target_field_key:
            det_field = det.get("targetFormFieldKey", "") or ""
            if det_field != target_field_key:
                continue

        # Transform to consistent output format with snake_case keys
        transformed = {
            "id": det.get("id"),
            "name": det.get("name"),
            "type": det.get("type"),
            "operator": det.get("operator"),
            "target_field_key": det.get("targetFormFieldKey"),
            "condition_summary": det.get("conditionSummary"),
        }

        # Add type-specific value fields
        if det.get("textValue") is not None:
            transformed["text_value"] = det.get("textValue")
        if det.get("selectValue") is not None:
            transformed["select_value"] = det.get("selectValue")
        if det.get("numericValue") is not None:
            transformed["numeric_value"] = det.get("numericValue")
        if det.get("booleanValue") is not None:
            transformed["boolean_value"] = det.get("booleanValue")
        if det.get("dateValue") is not None:
            transformed["date_value"] = det.get("dateValue")
        if det.get("isCurrentDate") is not None:
            transformed["is_current_date"] = det.get("isCurrentDate")

        filtered_determinants.append(transformed)

    # Sort by name for consistent ordering
    filtered_determinants.sort(key=lambda d: (d.get("name") or "").lower())

    # Apply limit
    total_matches = len(filtered_determinants)
    limited_determinants = filtered_determinants[:limit]

    # Build filters_applied for response
    filters_applied: dict[str, Any] = {}
    if name_pattern:
        filters_applied["name_pattern"] = name_pattern
    if determinant_type:
        filters_applied["determinant_type"] = determinant_type
    if operator:
        filters_applied["operator"] = operator
    if target_field_key:
        filters_applied["target_field_key"] = target_field_key

    return {
        "determinants": limited_determinants,
        "total": total_matches,
        "returned": len(limited_determinants),
        "service_id": service_id,
        "filters_applied": filters_applied,
    }


def register_determinant_tools(mcp: Any) -> None:
    """Register determinant tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Read operations
    mcp.tool()(determinant_list)
    mcp.tool()(determinant_get)
    mcp.tool()(determinant_search)
    # Write operations (audit-before-write pattern)
    mcp.tool()(textdeterminant_create)
    mcp.tool()(textdeterminant_update)
    mcp.tool()(selectdeterminant_create)
    mcp.tool()(numericdeterminant_create)
    mcp.tool()(booleandeterminant_create)
    mcp.tool()(datedeterminant_create)
    mcp.tool()(classificationdeterminant_create)
    mcp.tool()(griddeterminant_create)
    mcp.tool()(determinant_delete)

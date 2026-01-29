"""Component behaviour tools for BPA API.

This module provides MCP tools for managing component behaviours
in the BPA API. Component behaviours link determinants to form
components via effects that control component visibility, activation,
and other properties.

The BPA API does NOT have a direct endpoint to list all component
behaviours for a service. This module extracts behaviours from the
service export endpoint.

API Endpoints referenced:
- POST /download_service/{service_id} - Export service with componentBehaviours
- GET /service/{service_id}/behaviour/{component_key} - Get behaviour by component
- GET /behaviour/{id} - Get behaviour by ID
- POST /service/{service_id}/behaviour - Create component behaviour

Architecture (from bpa-determinants-research.md)::

    Form Component
        -> behaviourId -> componentBehaviours[id]
                            -> effects[]
                                -> jsonDeterminants (JSONLogic expression)
                                -> propertyEffects[]
                                    -> name: show|hide|enable|disable|etc.
                                    -> value: "true"|"false"
"""

from __future__ import annotations

import json
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
    "componentbehaviour_list",
    "componentbehaviour_get",
    "componentbehaviour_get_by_component",
    "effect_create",
    "effect_delete",
    "register_behaviour_tools",
]

# Valid effect types for property effects
VALID_EFFECT_TYPES = ["activate", "deactivate", "show", "hide", "enable", "disable"]

# Valid logic operators for combining determinants
VALID_LOGIC_OPERATORS = ["AND", "OR"]

# Mapping from BPA operator to JSONLogic operator
OPERATOR_MAPPING = {
    "EQUAL": "==",
    "NOT_EQUAL": "!=",
    "GREATER_THAN": ">",
    "LESS_THAN": "<",
    "GREATER_THAN_OR_EQUAL": ">=",
    "LESS_THAN_OR_EQUAL": "<=",
    "CONTAINS": "in",  # JSONLogic uses 'in' for contains
    "IS_EMPTY": "!",  # Will need special handling
    "IS_NOT_EMPTY": "!!",  # Will need special handling
}


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.behaviours'",
        "find_by_key": "jq '.behaviours[] | select(.component_key==\"x\")'",
        "with_effects": "jq '.behaviours[] | select(.effect_count > 0)'",
    },
)
async def componentbehaviour_list(service_id: str | int) -> dict[str, Any]:
    """List component behaviours for a service.

    Extracts behaviours from service export (no direct BPA endpoint exists).
    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        service_id: Service ID to list behaviours for.

    Returns:
        dict with behaviours (id, component_key, effect_count), total, service_id.
    """
    # Validate service_id
    if not service_id or (isinstance(service_id, str) and not service_id.strip()):
        raise ToolError(
            "'service_id' is required. Use 'service_list' to see available services."
        )

    try:
        async with BPAClient() as client:
            # First verify service exists
            try:
                await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Fetch service export to get componentBehaviours
            # Use minimal export options - only need behaviours data
            export_options = {
                "serviceSelected": True,
                "registrationsSelected": True,
                "determinantsSelected": True,
                "guideFormSelected": True,
                "applicantFormSelected": True,
                "sendFileFormSelected": True,
                "paymentFormSelected": True,
                "costsSelected": False,
                "requirementsSelected": False,
                "resultsSelected": False,
                "activityConditionsSelected": False,
                "registrationLawsSelected": False,
                "serviceLocationsSelected": False,
                "serviceTutorialsSelected": False,
                "serviceTranslationsSelected": False,
                "catalogsSelected": False,
                "rolesSelected": False,
                "printDocumentsSelected": False,
                "botsSelected": False,
                "copyService": False,
            }

            try:
                export_data, _ = await client.download_service(
                    str(service_id),
                    options=export_options,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)

    # Extract behaviours from export data
    behaviours = _extract_behaviours_from_export(export_data)

    return {
        "behaviours": behaviours,
        "total": len(behaviours),
        "service_id": str(service_id),
    }


async def componentbehaviour_get(behaviour_id: str) -> dict[str, Any]:
    """Get behaviour configuration with parsed JSONLogic determinants.

    Args:
        behaviour_id: Behaviour UUID.

    Returns:
        dict with id, component_key, service_id, effects (id, determinants,
        property_effects).
    """
    # Validate behaviour_id
    if not behaviour_id or (isinstance(behaviour_id, str) and not behaviour_id.strip()):
        raise ToolError(
            "'behaviour_id' is required. "
            "Use 'componentbehaviour_list' or 'form_component_get' "
            "to find behaviour IDs."
        )

    try:
        async with BPAClient() as client:
            try:
                data = await client.get(
                    "/behaviour/{id}",
                    path_params={"id": behaviour_id},
                    resource_type="behaviour",
                    resource_id=behaviour_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"Behaviour '{behaviour_id}' not found. "
                    "Use 'componentbehaviour_list' or 'form_component_get' "
                    "to find behaviour IDs."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="behaviour", resource_id=behaviour_id)

    return _transform_behaviour(data)


def _extract_behaviours_from_export(
    export_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract and transform component behaviours from service export.

    Args:
        export_data: Raw service export data from BPA API.

    Returns:
        list: List of behaviour summaries with id, component_key, effect_count.
    """
    behaviours: list[dict[str, Any]] = []

    # Handle nested service structure (live API wraps in 'service' key)
    data = export_data
    if "service" in export_data and isinstance(export_data["service"], dict):
        data = export_data["service"]

    # Get componentBehaviours array
    component_behaviours = data.get("componentBehaviours", [])

    if not isinstance(component_behaviours, list):
        return behaviours

    for behaviour in component_behaviours:
        if not isinstance(behaviour, dict):
            continue

        behaviour_id = behaviour.get("id")
        component_key = behaviour.get("componentKey")
        effects = behaviour.get("effects", [])

        # Count effects
        effect_count = len(effects) if isinstance(effects, list) else 0

        behaviours.append(
            {
                "id": behaviour_id,
                "component_key": component_key,
                "effect_count": effect_count,
            }
        )

    return behaviours


async def componentbehaviour_get_by_component(
    service_id: str | int,
    component_key: str,
) -> dict[str, Any]:
    """Get behaviour configuration for a component with parsed JSONLogic.

    Args:
        service_id: Service containing the component.
        component_key: Form component key.

    Returns:
        dict with id, component_key, service_id, effects (id, determinants,
        property_effects).
    """
    # Validate parameters
    if not service_id or (isinstance(service_id, str) and not service_id.strip()):
        raise ToolError(
            "'service_id' is required. Use 'service_list' to see available services."
        )

    comp_key_empty = isinstance(component_key, str) and not component_key.strip()
    if not component_key or comp_key_empty:
        raise ToolError(
            "'component_key' is required. Use 'form_get' to see component keys."
        )

    try:
        async with BPAClient() as client:
            try:
                data = await client.get(
                    "/service/{service_id}/behaviour/{component_key}",
                    path_params={
                        "service_id": service_id,
                        "component_key": component_key,
                    },
                    resource_type="behaviour",
                )
            except BPANotFoundError:
                raise ToolError(
                    f"No behaviour found for component '{component_key}' "
                    f"in service '{service_id}'. The component may not have "
                    "conditional logic configured."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="behaviour")

    # Pass service_id to transformer for context (AC1 requirement)
    return _transform_behaviour(data, service_id=service_id)


def _parse_jsonlogic_condition(condition: dict[str, Any]) -> dict[str, Any]:
    """Parse a single JSONLogic condition into readable format.

    Converts conditions like:
        {"==": [{"var": "data.field"}, value]}
    into:
        {"field": "data.field", "operator": "==", "value": value}

    Args:
        condition: A JSONLogic condition object.

    Returns:
        dict: Parsed condition with field, operator, value.
    """
    if not isinstance(condition, dict):
        return {"raw": condition}

    # Check for and/or logic operators (nested conditions)
    for logic_op in ["and", "or"]:
        if logic_op in condition:
            nested = condition[logic_op]
            if isinstance(nested, list):
                parsed_conditions = [_parse_jsonlogic_condition(c) for c in nested]
                return {
                    "logic": logic_op,
                    "conditions": parsed_conditions,
                }
            return {"logic": logic_op, "raw": nested}

    # Check for comparison operators
    comparison_ops = ["==", "!=", ">", "<", ">=", "<=", "in", "===", "!=="]
    for op in comparison_ops:
        if op in condition:
            args = condition[op]
            if isinstance(args, list) and len(args) >= 2:
                # First arg should be {"var": "data.field"}
                var_ref = args[0]
                value = args[1]

                field = None
                if isinstance(var_ref, dict) and "var" in var_ref:
                    field = var_ref["var"]
                elif isinstance(value, dict) and "var" in value:
                    # Swap if var is second
                    field = value["var"]
                    value = var_ref

                if field:
                    return {
                        "field": field,
                        "operator": op,
                        "value": value,
                    }
            return {"operator": op, "raw": args}

    # Check for unary operators (!, !!)
    if "!" in condition:
        arg = condition["!"]
        if isinstance(arg, list) and len(arg) == 1:
            arg = arg[0]
        if isinstance(arg, dict) and "var" in arg:
            return {
                "field": arg["var"],
                "operator": "isEmpty",
                "value": True,
            }
        return {"operator": "not", "raw": arg}

    if "!!" in condition:
        arg = condition["!!"]
        if isinstance(arg, list) and len(arg) == 1:
            arg = arg[0]
        if isinstance(arg, dict) and "var" in arg:
            return {
                "field": arg["var"],
                "operator": "isNotEmpty",
                "value": True,
            }
        return {"operator": "truthy", "raw": arg}

    # Check for 'if' conditions
    if "if" in condition:
        return {"operator": "if", "raw": condition["if"]}

    # Unknown structure - return as raw
    return {"raw": condition}


def _parse_jsonlogic_expression(expr: Any) -> list[dict[str, Any]]:
    """Parse a JSONLogic expression (which may be an array) into readable format.

    The jsonDeterminants field is typically a JSON string containing an array
    of JSONLogic expressions, e.g.:
        '[{"and": [{"==": [{"var": "data.field"}, true]}, ...]}]'

    Args:
        expr: Parsed JSON (list or dict) from jsonDeterminants.

    Returns:
        list: List of parsed determinant conditions.
    """
    if expr is None:
        return []

    # If it's a list, parse each element
    if isinstance(expr, list):
        return [_parse_jsonlogic_condition(item) for item in expr]

    # If it's a single dict, wrap in list
    if isinstance(expr, dict):
        return [_parse_jsonlogic_condition(expr)]

    # Return as raw for unexpected types
    return [{"raw": expr}]


def _parse_json_determinants(
    json_determinants: str | list[dict[str, Any]] | dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Parse jsonDeterminants field into readable structure.

    Handles:
    - String: Parse JSON first, then parse JSONLogic
    - List: Parse each JSONLogic expression
    - Dict: Parse single JSONLogic expression
    - None: Return empty list

    Args:
        json_determinants: Raw jsonDeterminants value from API.

    Returns:
        list: Parsed determinants with readable structure.
    """
    if json_determinants is None:
        return []

    # Parse string to JSON first
    if isinstance(json_determinants, str):
        if not json_determinants.strip():
            return []
        try:
            parsed = json.loads(json_determinants)
            return _parse_jsonlogic_expression(parsed)
        except json.JSONDecodeError:
            # Return raw string as fallback
            return [{"raw": json_determinants}]

    # Already parsed - process directly
    return _parse_jsonlogic_expression(json_determinants)


def _transform_behaviour(
    data: dict[str, Any], service_id: str | int | None = None
) -> dict[str, Any]:
    """Transform behaviour API response to snake_case format with readable JSONLogic.

    Args:
        data: Raw API response with camelCase keys.
        service_id: Optional service ID to include in response for context.
            If not provided, will attempt to extract from API response.

    Returns:
        dict: Transformed response with:
            - id: Behaviour UUID
            - component_key: Form component key
            - service_id: Service ID for context (if available)
            - effects: List with id, determinants (readable format), property_effects
    """
    effects: list[dict[str, Any]] = []

    raw_effects = data.get("effects", [])
    if isinstance(raw_effects, list):
        for effect in raw_effects:
            if not isinstance(effect, dict):
                continue

            # Parse jsonDeterminants into readable format
            json_determinants = effect.get("jsonDeterminants")
            parsed_determinants = _parse_json_determinants(json_determinants)

            # Transform property effects
            property_effects = []
            for pe in effect.get("propertyEffects", []):
                if isinstance(pe, dict):
                    property_effects.append(
                        {
                            "name": pe.get("name"),
                            "value": pe.get("value"),
                        }
                    )

            effects.append(
                {
                    "id": effect.get("id"),
                    "determinants": parsed_determinants,
                    "property_effects": property_effects,
                }
            )

    # Determine service_id: use provided value, or extract from API response
    resolved_service_id = service_id
    if resolved_service_id is None:
        # Try to extract from API response (may be serviceId or service_id)
        resolved_service_id = data.get("serviceId") or data.get("service_id")

    return {
        "id": data.get("id"),
        "component_key": data.get("componentKey"),
        "service_id": str(resolved_service_id) if resolved_service_id else None,
        "effects": effects,
    }


def _validate_effect_create_params(
    service_id: str | int,
    component_key: str,
    determinant_ids: list[str],
    logic: str,
    effect_type: str,
    effect_value: bool,
) -> None:
    """Validate effect_create parameters (pre-flight validation).

    Args:
        service_id: Service ID (required).
        component_key: Form component key (required).
        determinant_ids: List of determinant IDs (required, non-empty).
        logic: Logic operator (AND or OR).
        effect_type: Effect type (activate, deactivate, show, hide, enable, disable).
        effect_value: Boolean value for the effect.

    Raises:
        ToolError: If validation fails.
    """
    errors = []

    if not service_id or (isinstance(service_id, str) and not service_id.strip()):
        errors.append("'service_id' is required")

    if not component_key or (
        isinstance(component_key, str) and not component_key.strip()
    ):
        errors.append("'component_key' is required")

    if not determinant_ids:
        errors.append("'determinant_ids' must contain at least one determinant ID")
    elif not isinstance(determinant_ids, list):
        errors.append("'determinant_ids' must be a list of determinant IDs")
    elif len(determinant_ids) == 0:
        errors.append("'determinant_ids' must contain at least one determinant ID")

    if logic and logic.upper() not in VALID_LOGIC_OPERATORS:
        errors.append(f"'logic' must be one of: {', '.join(VALID_LOGIC_OPERATORS)}")

    if effect_type and effect_type.lower() not in VALID_EFFECT_TYPES:
        errors.append(f"'effect_type' must be one of: {', '.join(VALID_EFFECT_TYPES)}")

    if not isinstance(effect_value, bool):
        errors.append("'effect_value' must be a boolean (true or false)")

    if errors:
        error_msg = "; ".join(errors)
        raise ToolError(
            f"Cannot create effect: {error_msg}. "
            "Provide valid parameters for effect creation."
        )


def _build_condition_for_determinant(determinant: dict[str, Any]) -> dict[str, Any]:
    """Build a JSONLogic condition from a determinant.

    Args:
        determinant: Determinant data from BPA API.

    Returns:
        dict: JSONLogic condition object.
    """
    det_type = determinant.get("type", "text")
    target_field = determinant.get("targetFormFieldKey", "")
    operator = determinant.get("operator", "EQUAL")

    # Build the variable reference
    var_ref = {"var": f"data.{target_field}"}

    # Get the value based on determinant type
    if det_type == "boolean":
        value = determinant.get("booleanValue", True)
        return {"==": [var_ref, value]}

    elif det_type == "numeric":
        value = determinant.get("numericValue", 0)
        jsonlogic_op = OPERATOR_MAPPING.get(operator, "==")
        return {jsonlogic_op: [var_ref, value]}

    elif det_type in ("radio", "select"):
        value = determinant.get("selectValue", "")
        # For catalog/classification selections, may need .key suffix
        if "." not in target_field:
            var_ref = {"var": f"data.{target_field}.key"}
        jsonlogic_op = OPERATOR_MAPPING.get(operator, "==")
        return {jsonlogic_op: [var_ref, value]}

    elif det_type == "classification":
        value = determinant.get("classificationField", "")
        var_ref = {"var": f"data.{target_field}.key"}
        jsonlogic_op = OPERATOR_MAPPING.get(operator, "==")
        return {jsonlogic_op: [var_ref, value]}

    elif det_type == "date":
        is_current_date = determinant.get("isCurrentDate", False)
        if is_current_date:
            # For current date comparison, use special handling
            var_ref_date = {"var": f"data.{target_field}"}
            current_date = {"var": "_currentDate"}
            jsonlogic_op = OPERATOR_MAPPING.get(operator, "==")
            return {jsonlogic_op: [var_ref_date, current_date]}
        else:
            value = determinant.get("dateValue", "")
            jsonlogic_op = OPERATOR_MAPPING.get(operator, "==")
            return {jsonlogic_op: [var_ref, value]}

    else:  # text and others
        value = determinant.get("textValue", "")
        jsonlogic_op = OPERATOR_MAPPING.get(operator, "==")

        # Handle IS_EMPTY and IS_NOT_EMPTY specially
        if operator == "IS_EMPTY":
            return {"!": [var_ref]}
        elif operator == "IS_NOT_EMPTY":
            return {"!!": [var_ref]}

        return {jsonlogic_op: [var_ref, value]}


def _build_jsonlogic_for_determinants(
    determinants: list[dict[str, Any]], logic: str
) -> str:
    """Build stringified JSONLogic from multiple determinants.

    Args:
        determinants: List of determinant data from BPA API.
        logic: "AND" or "OR" for combining conditions.

    Returns:
        str: Stringified JSONLogic array (e.g., '[{"and": [...]}]')
    """
    conditions = []
    for det in determinants:
        condition = _build_condition_for_determinant(det)
        conditions.append(condition)

    # If only one condition, no need for and/or wrapper
    if len(conditions) == 1:
        jsonlogic = conditions
    else:
        # Wrap in and/or based on logic parameter
        logic_key = logic.lower()  # "and" or "or"
        jsonlogic = [{logic_key: conditions}]

    return json.dumps(jsonlogic)


async def _fetch_determinant_details(
    client: BPAClient, determinant_id: str
) -> dict[str, Any]:
    """Fetch determinant details from BPA API.

    Args:
        client: BPA client instance.
        determinant_id: ID of the determinant to fetch.

    Returns:
        dict: Determinant data from API.

    Raises:
        ToolError: If determinant not found.
    """
    try:
        return await client.get(
            "/determinant/{id}",
            path_params={"id": determinant_id},
            resource_type="determinant",
            resource_id=determinant_id,
        )
    except BPANotFoundError:
        raise ToolError(
            f"Determinant '{determinant_id}' not found. "
            "Use 'determinant_list' with service_id to see available determinants."
        )


async def _get_existing_behaviour(
    client: BPAClient, service_id: str | int, component_key: str
) -> dict[str, Any] | None:
    """Check if a behaviour already exists for a component.

    Args:
        client: BPA client instance.
        service_id: Service ID.
        component_key: Form component key.

    Returns:
        dict: Existing behaviour data, or None if not found.
    """
    try:
        return await client.get(
            "/service/{service_id}/behaviour/{component_key}",
            path_params={
                "service_id": service_id,
                "component_key": component_key,
            },
            resource_type="behaviour",
        )
    except BPANotFoundError:
        return None


async def effect_create(
    service_id: str | int,
    component_key: str,
    determinant_ids: list[str],
    logic: str = "AND",
    effect_type: str = "activate",
    effect_value: bool = True,
) -> dict[str, Any]:
    """Create effect linking determinants to a component. Audited write operation.

    Args:
        service_id: Parent service ID.
        component_key: Form component key to apply effect to.
        determinant_ids: Determinant IDs to combine (at least one).
        logic: "AND" (all match) or "OR" (any match). Default: "AND".
        effect_type: activate/deactivate/show/hide/enable/disable (default: activate).
        effect_value: Boolean value for effect (default: True).

    Returns:
        dict with behaviour_id, effect_id, component_key, determinant_count,
        effect_type, effect_value, logic, service_id, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_effect_create_params(
        service_id, component_key, determinant_ids, logic, effect_type, effect_value
    )

    # Normalize parameters
    logic = logic.upper()
    effect_type = effect_type.lower()

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
                    f"Cannot create effect: Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )

            # Fetch all determinant details to build JSONLogic
            determinants = []
            for det_id in determinant_ids:
                det_data = await _fetch_determinant_details(client, det_id)
                determinants.append(det_data)

            # Build JSONLogic expression
            json_determinants = _build_jsonlogic_for_determinants(determinants, logic)

            # Build property effect
            property_effect = {
                "name": effect_type,
                "type": "boolean",
                "value": "true" if effect_value else "false",
            }

            # Build the new effect
            new_effect = {
                "jsonDeterminants": json_determinants,
                "propertyEffects": [property_effect],
            }

            # Check if behaviour already exists for this component
            existing_behaviour = await _get_existing_behaviour(
                client, service_id, component_key
            )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="create",
                object_type="effect",
                params={
                    "service_id": str(service_id),
                    "component_key": component_key,
                    "determinant_ids": determinant_ids,
                    "logic": logic,
                    "effect_type": effect_type,
                    "effect_value": effect_value,
                    "existing_behaviour_id": existing_behaviour.get("id")
                    if existing_behaviour
                    else None,
                },
            )

            try:
                if existing_behaviour:
                    # Add effect to existing behaviour
                    existing_effects = existing_behaviour.get("effects", [])
                    existing_effects.append(new_effect)

                    payload = {
                        "id": existing_behaviour.get("id"),
                        "componentKey": component_key,
                        "effects": existing_effects,
                    }

                    # Update via PUT /behaviour
                    result = await client.put(
                        "/behaviour",
                        json=payload,
                        resource_type="behaviour",
                        resource_id=existing_behaviour.get("id"),
                    )

                    behaviour_id = existing_behaviour.get("id")
                else:
                    # Create new behaviour
                    payload = {
                        "componentKey": component_key,
                        "effects": [new_effect],
                    }

                    result = await client.post(
                        "/service/{service_id}/behaviour",
                        path_params={"service_id": service_id},
                        json=payload,
                        resource_type="behaviour",
                    )

                    behaviour_id = result.get("id")

                # Extract effect ID from result
                effects = result.get("effects", [])
                effect_id = None
                if effects:
                    # The new effect should be the last one
                    effect_id = effects[-1].get("id")

                # Save rollback state
                await audit_logger.save_rollback_state(
                    audit_id=audit_id,
                    object_type="effect",
                    object_id=str(effect_id) if effect_id else str(behaviour_id),
                    previous_state={
                        "behaviour_id": behaviour_id,
                        "effect_id": effect_id,
                        "component_key": component_key,
                        "service_id": str(service_id),
                        "was_new_behaviour": existing_behaviour is None,
                        "_operation": "create",
                    },
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "behaviour_id": behaviour_id,
                        "effect_id": effect_id,
                        "component_key": component_key,
                        "determinant_count": len(determinant_ids),
                    },
                )

                return {
                    "behaviour_id": behaviour_id,
                    "effect_id": effect_id,
                    "component_key": component_key,
                    "determinant_count": len(determinant_ids),
                    "effect_type": effect_type,
                    "effect_value": effect_value,
                    "logic": logic,
                    "service_id": str(service_id),
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(e, resource_type="behaviour")

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def _validate_effect_delete_params(behaviour_id: str) -> None:
    """Validate effect_delete parameters (pre-flight validation).

    Args:
        behaviour_id: Behaviour ID to delete (required).

    Raises:
        ToolError: If validation fails.
    """
    if not behaviour_id or (isinstance(behaviour_id, str) and not behaviour_id.strip()):
        raise ToolError(
            "'behaviour_id' is required. "
            "Use 'componentbehaviour_list' or 'componentbehaviour_get' "
            "to see available behaviours."
        )


async def effect_delete(behaviour_id: str) -> dict[str, Any]:
    """Delete a behaviour/effect from a component. Audited write operation.

    Args:
        behaviour_id: Behaviour UUID to delete.

    Returns:
        dict with deleted (bool), behaviour_id, deleted_behaviour, audit_id.
    """
    # Pre-flight validation (no audit record for validation failures)
    _validate_effect_delete_params(behaviour_id)

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
                    "/behaviour/{id}",
                    path_params={"id": behaviour_id},
                    resource_type="behaviour",
                    resource_id=behaviour_id,
                )
            except BPANotFoundError:
                raise ToolError(
                    f"[BEHAVIOUR_NOT_FOUND] Behaviour '{behaviour_id}' not found. "
                    "Use 'componentbehaviour_list' or 'componentbehaviour_get' "
                    "to see available behaviours."
                )

            # Create audit record BEFORE API call (audit-before-write pattern)
            audit_logger = AuditLogger()
            audit_id = await audit_logger.record_pending(
                user_email=user_email,
                operation_type="delete",
                object_type="behaviour",
                object_id=str(behaviour_id),
                params={},
            )

            # Save rollback state for undo capability
            await audit_logger.save_rollback_state(
                audit_id=audit_id,
                object_type="behaviour",
                object_id=str(behaviour_id),
                previous_state=previous_state,  # Full state for recreation
            )

            try:
                await client.delete(
                    "/behaviour/{behaviour_id}",
                    path_params={"behaviour_id": behaviour_id},
                    resource_type="behaviour",
                    resource_id=behaviour_id,
                )

                # Mark audit as success
                await audit_logger.mark_success(
                    audit_id,
                    result={
                        "deleted": True,
                        "behaviour_id": str(behaviour_id),
                    },
                )

                return {
                    "deleted": True,
                    "behaviour_id": str(behaviour_id),
                    "deleted_behaviour": {
                        "id": previous_state.get("id"),
                        "component_key": previous_state.get("componentKey"),
                        "effect_count": len(previous_state.get("effects", [])),
                    },
                    "audit_id": audit_id,
                }

            except BPAClientError as e:
                # Mark audit as failed
                await audit_logger.mark_failed(audit_id, str(e))
                raise translate_error(
                    e, resource_type="behaviour", resource_id=behaviour_id
                )

    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="behaviour", resource_id=behaviour_id)


def register_behaviour_tools(mcp: Any) -> None:
    """Register behaviour tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(componentbehaviour_list)
    mcp.tool()(componentbehaviour_get)
    mcp.tool()(componentbehaviour_get_by_component)
    mcp.tool()(effect_create)
    mcp.tool()(effect_delete)

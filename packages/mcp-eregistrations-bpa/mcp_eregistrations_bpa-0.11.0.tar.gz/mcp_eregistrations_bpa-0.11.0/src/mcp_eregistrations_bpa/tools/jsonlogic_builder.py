"""JSONLogic Builder Helper for BPA determinant conditions.

This module provides internal helper functions for building complex JSONLogic
expressions from nested AND/OR condition trees. It is NOT an MCP tool - it is
an internal utility used by effect_create and other determinant-related tools.

The output format matches BPA's jsonDeterminants field which contains a
stringified JSON array of JSONLogic expressions.

Example output format:
    [{"and": [{"==": [{"var": "data.fieldKey"}, true]}, {"or": [...]}]}]

JSONLogic operators supported:
    - and: All conditions must be true
    - or: At least one condition must be true
    - ==: Equality comparison
    - !=: Inequality comparison
    - >, <, >=, <=: Numeric comparisons
    - var: Variable reference (e.g., data.fieldKey)

Usage:
    from mcp_eregistrations_bpa.tools.jsonlogic_builder import (
        build_jsonlogic,
        Condition,
        ConditionGroup,
    )

    # Simple condition
    condition = Condition(
        field_key="applicantName",
        operator="==",
        value="John",
    )
    jsonlogic = build_jsonlogic(condition)

    # Nested AND/OR conditions
    group = ConditionGroup(
        logic="and",
        conditions=[
            Condition(field_key="age", operator=">=", value=18),
            ConditionGroup(
                logic="or",
                conditions=[
                    Condition(field_key="status", operator="==", value="approved"),
                    Condition(field_key="status", operator="==", value="pending"),
                ],
            ),
        ],
    )
    jsonlogic = build_jsonlogic(group)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Union

__all__ = [
    "Condition",
    "ConditionGroup",
    "DeterminantRef",
    "build_jsonlogic",
    "build_jsonlogic_string",
    "build_from_dict",
    "build_jsonlogic_from_dict",
    "parse_jsonlogic_string",
    "validate_condition_tree",
    "JSONLogicError",
    "LogicOperator",
    "ComparisonOperator",
    "DEFAULT_MAX_DEPTH",
]


class JSONLogicError(Exception):
    """Error raised when JSONLogic building or validation fails."""


# Default maximum nesting depth for condition trees
DEFAULT_MAX_DEPTH = 10


# Type aliases for clarity
LogicOperator = Literal["and", "or"]
ComparisonOperator = Literal["==", "!=", ">", "<", ">=", "<="]


@dataclass
class Condition:
    """A single condition comparing a field value.

    Attributes:
        field_key: The form field key (e.g., "applicantName").
            Will be prefixed with "data." for var reference.
        operator: Comparison operator (==, !=, >, <, >=, <=).
        value: The value to compare against (string, number, bool, or None).
        use_key_suffix: If True, appends ".key" to field_key for catalog fields.
            Default False.
    """

    field_key: str
    operator: ComparisonOperator
    value: Any
    use_key_suffix: bool = False

    def __post_init__(self) -> None:
        """Validate condition after initialization."""
        if not self.field_key or not self.field_key.strip():
            raise JSONLogicError("Condition field_key is required and cannot be empty")
        valid_operators = ("==", "!=", ">", "<", ">=", "<=")
        if self.operator not in valid_operators:
            raise JSONLogicError(
                f"Invalid operator '{self.operator}'. "
                f"Must be one of: {', '.join(valid_operators)}"
            )

    def to_jsonlogic(self) -> dict[str, Any]:
        """Convert condition to JSONLogic expression.

        Returns:
            JSONLogic dict like {"==": [{"var": "data.fieldKey"}, value]}
        """
        var_path = f"data.{self.field_key}"
        if self.use_key_suffix:
            var_path += ".key"

        return {self.operator: [{"var": var_path}, self.value]}


@dataclass
class DeterminantRef:
    """Reference to an existing determinant by ID.

    Use this when you want to include an existing determinant
    in a condition tree. The actual condition logic will be
    resolved from the determinant.

    Attributes:
        determinant_id: UUID of the existing determinant.
        field_key: The form field key the determinant targets.
            Required to build the var reference.
        operator: The comparison operator from the determinant.
        value: The comparison value from the determinant.
        use_key_suffix: If True, appends ".key" for catalog fields.
    """

    determinant_id: str
    field_key: str
    operator: ComparisonOperator
    value: Any
    use_key_suffix: bool = False

    def __post_init__(self) -> None:
        """Validate determinant reference after initialization."""
        if not self.determinant_id or not self.determinant_id.strip():
            raise JSONLogicError(
                "DeterminantRef determinant_id is required and cannot be empty"
            )
        if not self.field_key or not self.field_key.strip():
            raise JSONLogicError(
                "DeterminantRef field_key is required to build condition"
            )
        valid_operators = ("==", "!=", ">", "<", ">=", "<=")
        if self.operator not in valid_operators:
            raise JSONLogicError(
                f"Invalid operator '{self.operator}' in DeterminantRef. "
                f"Must be one of: {', '.join(valid_operators)}"
            )

    def to_jsonlogic(self) -> dict[str, Any]:
        """Convert determinant reference to JSONLogic expression.

        Returns:
            JSONLogic dict like {"==": [{"var": "data.fieldKey"}, value]}
        """
        var_path = f"data.{self.field_key}"
        if self.use_key_suffix:
            var_path += ".key"

        return {self.operator: [{"var": var_path}, self.value]}


# Type for items in a condition group
ConditionItem = Union[Condition, DeterminantRef, "ConditionGroup"]


@dataclass
class ConditionGroup:
    """A group of conditions combined with AND/OR logic.

    Supports nesting for complex expressions like:
    AND(condition1, OR(condition2, condition3))

    Attributes:
        logic: The combining logic ("and" or "or").
        conditions: List of conditions, determinant refs, or nested groups.
    """

    logic: LogicOperator
    conditions: list[ConditionItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate condition group after initialization."""
        if self.logic not in ("and", "or"):
            raise JSONLogicError(
                f"Invalid logic operator '{self.logic}'. Must be 'and' or 'or'"
            )
        if not self.conditions:
            raise JSONLogicError(
                f"ConditionGroup with '{self.logic}' logic "
                "requires at least one condition"
            )

    def to_jsonlogic(self) -> dict[str, Any]:
        """Convert condition group to JSONLogic expression.

        Returns:
            JSONLogic dict like {"and": [expr1, expr2, ...]}
        """
        expressions = []
        for condition in self.conditions:
            expressions.append(condition.to_jsonlogic())

        return {self.logic: expressions}


def validate_condition_tree(
    condition: ConditionItem,
    max_depth: int = DEFAULT_MAX_DEPTH,
    _current_depth: int = 0,
) -> list[str]:
    """Validate a condition tree for correctness.

    Checks:
    - Maximum nesting depth (prevents infinite recursion)
    - All conditions have required fields
    - All operators are valid

    Args:
        condition: The root condition or group to validate.
        max_depth: Maximum allowed nesting depth. Default 10.
        _current_depth: Internal counter for recursion depth.

    Returns:
        List of validation error messages. Empty list if valid.
    """
    errors: list[str] = []

    if _current_depth > max_depth:
        errors.append(
            f"Condition tree exceeds maximum depth of {max_depth}. "
            "Simplify the condition structure."
        )
        return errors

    if isinstance(condition, Condition | DeterminantRef):
        # Individual conditions are validated in __post_init__
        try:
            condition.to_jsonlogic()  # Test serialization
        except Exception as e:
            errors.append(f"Invalid condition: {e}")

    elif isinstance(condition, ConditionGroup):
        # Note: empty conditions already validated in __post_init__,
        # but we check here for programmatically constructed groups
        for i, sub_condition in enumerate(condition.conditions):
            sub_errors = validate_condition_tree(
                sub_condition, max_depth, _current_depth + 1
            )
            for error in sub_errors:
                errors.append(f"conditions[{i}]: {error}")

    else:
        errors.append(
            f"Unknown condition type: {type(condition).__name__}. "
            "Expected Condition, DeterminantRef, or ConditionGroup."
        )

    return errors


def build_jsonlogic(condition: ConditionItem) -> list[dict[str, Any]]:
    """Build JSONLogic expression from a condition tree.

    The output is a list containing the JSONLogic expression,
    matching BPA's expected format.

    Args:
        condition: A Condition, DeterminantRef, or ConditionGroup.

    Returns:
        List containing the JSONLogic expression dict.
        Example: [{"and": [{"==": [{"var": "data.field"}, "value"]}, ...]}]

    Raises:
        JSONLogicError: If the condition tree is invalid.
    """
    # Validate first
    errors = validate_condition_tree(condition)
    if errors:
        raise JSONLogicError(f"Invalid condition tree: {'; '.join(errors)}")

    return [condition.to_jsonlogic()]


def build_jsonlogic_string(condition: ConditionItem) -> str:
    """Build JSONLogic expression and serialize to string.

    This produces the exact format expected by BPA's jsonDeterminants field.

    Args:
        condition: A Condition, DeterminantRef, or ConditionGroup.

    Returns:
        Stringified JSON array of JSONLogic expressions.
        Example: '[{"and":[{"==":[{"var":"data.field"},"value"]}]}]'

    Raises:
        JSONLogicError: If the condition tree is invalid.
    """
    jsonlogic = build_jsonlogic(condition)
    return json.dumps(jsonlogic, separators=(",", ":"))


def parse_jsonlogic_string(jsonlogic_str: str) -> list[dict[str, Any]]:
    """Parse a JSONLogic string back to a Python structure.

    Useful for inspecting or modifying existing JSONLogic expressions.

    Args:
        jsonlogic_str: Stringified JSONLogic from BPA.

    Returns:
        Parsed list of JSONLogic expression dicts.

    Raises:
        JSONLogicError: If parsing fails.
    """
    if not jsonlogic_str or not jsonlogic_str.strip():
        return []

    try:
        parsed = json.loads(jsonlogic_str)
        if not isinstance(parsed, list):
            raise JSONLogicError(
                f"JSONLogic must be a list of expressions. Got {type(parsed).__name__}."
            )
        return parsed
    except json.JSONDecodeError as e:
        raise JSONLogicError(
            f"Failed to parse JSONLogic string: {e}. Ensure the string is valid JSON."
        )


def build_from_dict(
    condition_dict: dict[str, Any],
    _current_depth: int = 0,
) -> ConditionItem:
    """Build a condition tree from a dictionary structure.

    This allows building conditions from JSON/dict input,
    useful for API integrations.

    Args:
        condition_dict: Dict with structure like:
            {"and": [{"determinant_id": "..."}, {"or": [...]}]}
            or
            {"field_key": "...", "operator": "==", "value": "..."}
        _current_depth: Internal counter for recursion depth (do not set manually).

    Returns:
        Condition, DeterminantRef, or ConditionGroup.

    Raises:
        JSONLogicError: If the dict structure is invalid or exceeds max depth.

    Example:
        condition_dict = {
            "and": [
                {
                    "determinant_id": "det-1",
                    "field_key": "f1",
                    "operator": "==",
                    "value": True,
                },
                {
                    "or": [
                        {"field_key": "status", "operator": "==", "value": "approved"},
                        {"field_key": "status", "operator": "==", "value": "pending"}
                    ]
                }
            ]
        }
        condition = build_from_dict(condition_dict)
    """
    # Prevent infinite recursion from malformed input
    if _current_depth > DEFAULT_MAX_DEPTH:
        raise JSONLogicError(
            f"Condition dict exceeds maximum nesting depth of {DEFAULT_MAX_DEPTH}. "
            "Simplify the condition structure."
        )

    if not isinstance(condition_dict, dict):
        raise JSONLogicError(f"Expected dict, got {type(condition_dict).__name__}")

    # Check for logic operators (and/or)
    if "and" in condition_dict:
        items = condition_dict["and"]
        if not isinstance(items, list):
            raise JSONLogicError("'and' value must be a list of conditions")
        return ConditionGroup(
            logic="and",
            conditions=[build_from_dict(item, _current_depth + 1) for item in items],
        )

    if "or" in condition_dict:
        items = condition_dict["or"]
        if not isinstance(items, list):
            raise JSONLogicError("'or' value must be a list of conditions")
        return ConditionGroup(
            logic="or",
            conditions=[build_from_dict(item, _current_depth + 1) for item in items],
        )

    # Check for determinant reference
    if "determinant_id" in condition_dict:
        return DeterminantRef(
            determinant_id=condition_dict["determinant_id"],
            field_key=condition_dict.get("field_key", ""),
            operator=condition_dict.get("operator", "=="),
            value=condition_dict.get("value"),
            use_key_suffix=condition_dict.get("use_key_suffix", False),
        )

    # Check for simple condition
    if "field_key" in condition_dict:
        return Condition(
            field_key=condition_dict["field_key"],
            operator=condition_dict.get("operator", "=="),
            value=condition_dict.get("value"),
            use_key_suffix=condition_dict.get("use_key_suffix", False),
        )

    raise JSONLogicError(
        "Invalid condition dict. Must contain 'and', 'or', "
        "'determinant_id', or 'field_key'."
    )


def build_jsonlogic_from_dict(condition_dict: dict[str, Any]) -> str:
    """Convenience function to build JSONLogic string from dict.

    Combines build_from_dict and build_jsonlogic_string.

    Args:
        condition_dict: Dict structure of conditions.

    Returns:
        Stringified JSONLogic for BPA.

    Raises:
        JSONLogicError: If the structure is invalid.
    """
    condition = build_from_dict(condition_dict)
    return build_jsonlogic_string(condition)

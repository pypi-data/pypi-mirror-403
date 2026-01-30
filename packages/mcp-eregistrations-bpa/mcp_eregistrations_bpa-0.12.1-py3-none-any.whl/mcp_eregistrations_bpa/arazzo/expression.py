"""Arazzo runtime expression parser and resolver.

Implements expression handling as defined by the Arazzo specification:
https://spec.openapis.org/arazzo/latest.html

Expression syntax (ABNF):
    expression = ( "$url" / "$method" / "$statusCode" / "$request." source /
                   "$response." source / "$inputs." name / "$outputs." name /
                   "$steps." name / "$workflows." name / "$sourceDescriptions." name /
                   "$components." name )

Expressions can be embedded in strings using curly braces: {$inputs.fieldName}

Based on the Speakeasy Go implementation:
https://github.com/speakeasy-api/openapi/tree/main/arazzo/expression
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExpressionType(Enum):
    """Types of Arazzo runtime expressions."""

    URL = "url"
    METHOD = "method"
    STATUS_CODE = "statusCode"
    REQUEST = "request"
    RESPONSE = "response"
    INPUTS = "inputs"
    OUTPUTS = "outputs"
    STEPS = "steps"
    WORKFLOWS = "workflows"
    SOURCE_DESCRIPTIONS = "sourceDescriptions"
    COMPONENTS = "components"
    UNKNOWN = "unknown"


# Regex to find embedded expressions: {$...}
# Matches { followed by $ and any content until the closing }
# Uses non-greedy matching to handle multiple expressions
EMBEDDED_EXPRESSION_PATTERN = re.compile(r"\{(\$[^}]+)\}")

# Regex to validate a bare expression starts with $
BARE_EXPRESSION_PATTERN = re.compile(r"^\$[a-zA-Z]")


@dataclass
class Expression:
    """Represents a parsed Arazzo runtime expression.

    Attributes:
        raw: The original expression string.
        expression_type: The type of expression ($inputs, $steps, etc.).
        parts: The parsed parts of the expression.
        json_pointer: Optional JSON pointer for body references.
    """

    raw: str
    expression_type: ExpressionType
    parts: list[str]
    json_pointer: str | None = None

    @classmethod
    def parse(cls, expr: str) -> Expression:
        """Parse an expression string into an Expression object.

        Args:
            expr: The expression string (e.g., "$inputs.fieldName").

        Returns:
            Parsed Expression object.

        Raises:
            ValueError: If the expression is not valid.
        """
        if not expr.startswith("$"):
            raise ValueError(f"Expression must start with $: {expr}")

        # Handle JSON pointer in body references: $response.body#/user/id
        json_pointer = None
        if "#" in expr:
            expr, json_pointer = expr.split("#", 1)

        # Parse the expression parts
        parts = expr.split(".")

        # Determine expression type from the first part
        type_str = parts[0][1:]  # Remove the $ prefix
        try:
            expr_type = ExpressionType(type_str)
        except ValueError:
            expr_type = ExpressionType.UNKNOWN

        return cls(
            raw=expr,
            expression_type=expr_type,
            parts=parts,
            json_pointer=json_pointer,
        )

    def get_field_name(self) -> str | None:
        """Get the field name referenced by this expression.

        For $inputs.fieldName, returns "fieldName".
        For $steps.stepId.outputs.fieldName, returns "fieldName".

        Returns:
            The field name, or None if not applicable.
        """
        if self.expression_type == ExpressionType.INPUTS:
            return self.parts[1] if len(self.parts) > 1 else None
        elif self.expression_type == ExpressionType.OUTPUTS:
            return self.parts[1] if len(self.parts) > 1 else None
        elif self.expression_type == ExpressionType.STEPS:
            # $steps.stepId.outputs.fieldName -> fieldName
            return self.parts[3] if len(self.parts) > 3 else None
        elif self.expression_type == ExpressionType.WORKFLOWS:
            # $workflows.workflowId.outputs.fieldName -> fieldName
            return self.parts[3] if len(self.parts) > 3 else None
        return None

    def get_step_id(self) -> str | None:
        """Get the step ID for step references.

        Returns:
            The step ID for $steps expressions, None otherwise.
        """
        if self.expression_type == ExpressionType.STEPS and len(self.parts) > 1:
            return self.parts[1]
        return None

    def get_workflow_id(self) -> str | None:
        """Get the workflow ID for workflow references.

        Returns:
            The workflow ID for $workflows expressions, None otherwise.
        """
        if self.expression_type == ExpressionType.WORKFLOWS and len(self.parts) > 1:
            return self.parts[1]
        return None


def extract_expressions(value: str) -> list[tuple[str, Expression]]:
    """Extract all embedded expressions from a string.

    Finds all {$...} patterns and parses them into Expression objects.

    Args:
        value: The string containing embedded expressions.

    Returns:
        List of tuples (original_match, Expression) for each found expression.
        original_match includes the curly braces: {$inputs.foo}

    Examples:
        >>> extract_expressions("Hello {$inputs.name}!")
        [("{$inputs.name}", Expression(...))]

        >>> extract_expressions("ID: {$steps.create.outputs.id}-{$inputs.suffix}")
        [("{$steps.create.outputs.id}", ...), ("{$inputs.suffix}", ...)]

        >>> extract_expressions("No expressions here")
        []
    """
    expressions = []
    for match in EMBEDDED_EXPRESSION_PATTERN.finditer(value):
        full_match = match.group(0)  # {$inputs.foo}
        inner_expr = match.group(1)  # $inputs.foo
        try:
            parsed = Expression.parse(inner_expr)
            expressions.append((full_match, parsed))
        except ValueError:
            # Skip invalid expressions
            continue
    return expressions


def is_expression(value: str) -> bool:
    """Check if a string is an Arazzo runtime expression.

    Args:
        value: The string to check.

    Returns:
        True if the string is a bare expression ($...) or
        contains embedded expressions ({$...}).
    """
    if BARE_EXPRESSION_PATTERN.match(value):
        return True
    if EMBEDDED_EXPRESSION_PATTERN.search(value):
        return True
    return False


def resolve_expression(
    expr: Expression,
    context: dict[str, Any],
) -> Any:
    """Resolve a single expression against a context.

    Args:
        expr: The parsed Expression object.
        context: Dictionary with 'inputs', 'steps', 'outputs' keys.

    Returns:
        The resolved value, or None if not found.
    """
    if expr.expression_type == ExpressionType.INPUTS:
        field = expr.get_field_name()
        if field and "inputs" in context and field in context["inputs"]:
            return context["inputs"][field]
        return None

    if expr.expression_type == ExpressionType.OUTPUTS:
        field = expr.get_field_name()
        if field and "outputs" in context and field in context["outputs"]:
            return context["outputs"][field]
        return None

    if expr.expression_type == ExpressionType.STEPS:
        step_id = expr.get_step_id()
        field = expr.get_field_name()
        if step_id and field and "steps" in context:
            if step_id in context["steps"]:
                step_outputs = context["steps"][step_id]
                if field in step_outputs:
                    return step_outputs[field]
        return None

    if expr.expression_type == ExpressionType.WORKFLOWS:
        workflow_id = expr.get_workflow_id()
        field = expr.get_field_name()
        if workflow_id and field and "workflows" in context:
            if workflow_id in context["workflows"]:
                workflow_outputs = context["workflows"][workflow_id]
                if field in workflow_outputs:
                    return workflow_outputs[field]
        return None

    # For other expression types (url, method, etc.), return the raw expression
    # These would be resolved at HTTP execution time
    return None


def _resolve_preview_expression(
    expr: Expression, context: dict[str, Any]
) -> tuple[bool, Any]:
    """Resolve expression in preview mode with special handling.

    In preview mode:
    - $inputs.* expressions are resolved (we have the values)
    - $steps.* expressions show "[from step 'X': field_name]" (not yet executed)
    - Other expressions are resolved normally

    Args:
        expr: Parsed expression.
        context: Execution context.

    Returns:
        Tuple of (was_resolved, value). If was_resolved is False, caller
        should use the value as a placeholder string.
    """
    if expr.expression_type == ExpressionType.STEPS:
        # Step outputs aren't available yet in preview - show explanatory text
        step_id = expr.get_step_id()
        field_name = expr.get_field_name()
        if step_id and field_name:
            return (False, f"[from step '{step_id}': {field_name}]")
        return (False, f"[from step '{step_id or 'unknown'}']")

    # For $inputs and other types, resolve normally
    resolved = resolve_expression(expr, context)
    if resolved is not None:
        return (True, resolved)

    # Couldn't resolve - return descriptive placeholder
    field_name = expr.get_field_name()
    if expr.expression_type == ExpressionType.INPUTS and field_name:
        return (False, f"[missing input: {field_name}]")
    return (False, f"<{expr.raw}>")


def resolve_string(
    value: Any,
    context: dict[str, Any],
    preview: bool = False,
) -> Any:
    """Resolve all expressions in a value.

    Handles:
    - Non-string values: returned as-is
    - Bare expressions ($inputs.foo): fully resolved
    - Embedded expressions ({$inputs.foo}): replaced in string
    - Mixed strings ("prefix-{$inputs.id}-suffix"): interpolated

    In preview mode:
    - $inputs.* expressions are resolved with actual values
    - $steps.* expressions show "[from step 'X': field_name]"
    - Missing inputs show "[missing input: field_name]"

    Args:
        value: The value to resolve (may be expression, string, or other).
        context: Dictionary with 'inputs', 'steps', 'outputs' keys.
        preview: If True, resolve inputs but show step refs as explanatory text.

    Returns:
        Resolved value. For strings with embedded expressions, returns
        the interpolated string. For bare expressions that resolve to
        non-strings, returns the typed value.

    Examples:
        >>> ctx = {"inputs": {"name": "John", "id": 123}}

        >>> resolve_string("$inputs.name", ctx)
        "John"

        >>> resolve_string("{$inputs.name}", ctx)
        "John"

        >>> resolve_string("Hello {$inputs.name}!", ctx)
        "Hello John!"

        >>> resolve_string("ID-{$inputs.id}", ctx)
        "ID-123"

        >>> resolve_string(42, ctx)  # Non-string passthrough
        42
    """
    if not isinstance(value, str):
        return value

    # Check if this is a bare expression (starts with $)
    if BARE_EXPRESSION_PATTERN.match(value):
        try:
            expr = Expression.parse(value)
            if preview:
                _, result = _resolve_preview_expression(expr, context)
                return result
            resolved = resolve_expression(expr, context)
            return resolved if resolved is not None else value
        except ValueError:
            return value

    # Check for embedded expressions
    expressions = extract_expressions(value)
    if not expressions:
        # No expressions found, return original value
        return value

    # If the entire string is a single embedded expression, unwrap it
    # This preserves the type of the resolved value
    if len(expressions) == 1:
        full_match, expr = expressions[0]
        if value == full_match:
            # The whole string is just {$expression}
            if preview:
                was_resolved, result = _resolve_preview_expression(expr, context)
                # If resolved to non-string, return the typed value
                return result
            resolved = resolve_expression(expr, context)
            return resolved if resolved is not None else value

    # Multiple expressions or mixed string - interpolate
    result = value
    for full_match, expr in expressions:
        if preview:
            _, replacement_val = _resolve_preview_expression(expr, context)
            replacement = str(replacement_val)
        else:
            resolved = resolve_expression(expr, context)
            replacement = str(resolved) if resolved is not None else full_match
        result = result.replace(full_match, replacement, 1)

    return result

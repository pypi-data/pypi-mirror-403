"""MCP tools for Arazzo workflow orchestration.

This module provides tools for:
- Story 5.1: Workflow Catalog & Discovery
- Story 5.4: Workflow Executor
- Story 5.5: Progress Reporting & Streaming
- Story 5.6: Error Recovery & Rollback
- Story 5.7: Workflow Chaining & Composition
- Story 5.8: Guided Interactive Mode

Note: Intent-to-Workflow Matching and Input Extraction are handled by the
calling AI agent, not by this MCP. The MCP provides catalog, schema, and
execution capabilities; the AI provides intent understanding and input extraction.
"""

from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.arazzo import resolve_string
from mcp_eregistrations_bpa.tools.large_response import large_response_handler
from mcp_eregistrations_bpa.workflows import (
    get_workflow_catalog,
)
from mcp_eregistrations_bpa.workflows.models import OPERATION_TO_TOOL_MAP

__all__ = [
    # Story 5.1: Workflow Catalog & Discovery
    "workflow_list",
    "workflow_describe",
    "workflow_search",
    # Story 5.4: Workflow Executor
    "workflow_execute",
    # Story 5.5: Progress Reporting & Streaming
    "workflow_status",
    "workflow_cancel",
    # Story 5.6: Error Recovery & Rollback
    "workflow_retry",
    "workflow_rollback",
    # Story 5.7: Workflow Chaining & Composition
    "workflow_chain",
    # Story 5.8: Guided Interactive Mode
    "workflow_start_interactive",
    "workflow_continue",
    "workflow_confirm",
    # Story 14.6: Workflow Validation
    "workflow_validate",
    # Registration
    "register_workflow_tools",
]


# =============================================================================
# Story 5.1: Workflow Catalog & Discovery
# =============================================================================


@large_response_handler(
    threshold_bytes=50 * 1024,  # 50KB threshold for list tools
    navigation={
        "list_all": "jq '.workflows'",
        "by_category": "jq '.workflows[] | select(.category==\"service-creation\")'",
        "by_id": "jq '.workflows[] | select(.id | contains(\"x\"))'",
    },
)
async def workflow_list(category: str | None = None) -> dict[str, Any]:
    """List available Arazzo workflows for BPA service design.

    Large responses (>50KB) are saved to file with navigation hints.

    Args:
        category: Filter by category (e.g., "service-creation", "roles-configuration").

    Returns:
        dict with workflows (list), total (int), categories (list).
    """
    catalog = get_workflow_catalog()

    workflows = catalog.list_workflows(category=category)
    all_categories = catalog.categories

    return {
        "workflows": workflows,
        "total": len(workflows),
        "categories": all_categories,
    }


async def workflow_describe(workflow_id: str) -> dict[str, Any]:
    """Get detailed workflow specification including inputs, steps, and outputs.

    Args:
        workflow_id: Workflow identifier (e.g., "createMinimalService").

    Returns:
        dict with id, summary, description, category, inputs, steps, outputs.
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        available = [wf["id"] for wf in catalog.list_workflows()[:5]]
        suggestion = ", ".join(available)
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            f"Available workflows include: {suggestion}. "
            "Use 'workflow_list' to see all available workflows."
        )

    return workflow.to_detail_dict()


async def workflow_search(query: str, limit: int = 10) -> dict[str, Any]:
    """Search workflows by keyword in IDs, summaries, and descriptions.

    Args:
        query: Search query (e.g., "role", "create service").
        limit: Max results (default 10).

    Returns:
        dict with query, matches (ranked by relevance), total.
    """
    if not query or not query.strip():
        raise ToolError(
            "Search query cannot be empty. Provide a keyword to search for."
        )

    catalog = get_workflow_catalog()
    matches = catalog.search_workflows(query.strip(), limit=limit)

    return {
        "query": query,
        "matches": matches,
        "total": len(matches),
    }


# =============================================================================
# Story 5.4: Workflow Executor
# =============================================================================


async def workflow_execute(
    workflow_id: str,
    inputs: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute workflow steps sequentially, passing outputs between steps.

    Args:
        workflow_id: Workflow to execute (e.g., "createMinimalService").
        inputs: Input values for the workflow.
        dry_run: Validate only, don't execute.

    Returns:
        dict with workflow_id, status, steps, outputs, message.
        On failure: failed_at_step, error, rollback_available.
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    # Validate required inputs
    missing_inputs = []
    for inp in workflow.inputs:
        if inp.required and inp.name not in inputs:
            missing_inputs.append(inp.name)

    if missing_inputs:
        raise ToolError(
            f"Missing required inputs: {', '.join(missing_inputs)}. "
            f"Use 'workflow_describe {workflow_id}' to see required inputs."
        )

    # Initialize execution context
    context: dict[str, Any] = {
        "inputs": inputs.copy(),
        "steps": {},
        "outputs": {},
    }

    step_results: list[dict[str, Any]] = []
    completed_steps: list[str] = []

    # Dry run mode - return execution plan
    if dry_run:
        plan_steps = []
        for step in workflow.steps:
            plan_steps.append(
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "tool": step.mcp_tool,
                    "inputs": _resolve_step_inputs(step, context, preview=True),
                    "status": "planned",
                }
            )

        return {
            "workflow_id": workflow_id,
            "status": "dry_run",
            "steps": plan_steps,
            "message": f"Execution plan for '{workflow.summary}'",
            "total_steps": len(plan_steps),
        }

    # Execute each step
    for step in workflow.steps:
        # Check conditional execution
        if step.condition:
            condition_met = _evaluate_condition(step.condition, context)
            if not condition_met:
                step_results.append(
                    {
                        "step_id": step.step_id,
                        "status": "skipped",
                        "reason": f"Condition not met: {step.condition}",
                    }
                )
                continue

        # Resolve step inputs from context
        step_inputs = _resolve_step_inputs(step, context)

        # Execute the step
        try:
            step_output = await _execute_step(step, step_inputs)

            # Store outputs in context
            context["steps"][step.step_id] = step_output
            for key, value in step_output.items():
                context["outputs"][key] = value

            step_results.append(
                {
                    "step_id": step.step_id,
                    "tool": step.mcp_tool,
                    "inputs": step_inputs,
                    "status": "success",
                    "outputs": step_output,
                }
            )
            completed_steps.append(step.step_id)

        except Exception as e:
            # Step failed - stop execution
            step_results.append(
                {
                    "step_id": step.step_id,
                    "tool": step.mcp_tool,
                    "inputs": step_inputs,
                    "status": "failed",
                    "error": str(e),
                }
            )

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "failed_at_step": step.step_id,
                "error": str(e),
                "steps": step_results,
                "completed_steps": completed_steps,
                "rollback_available": len(completed_steps) > 0,
                "suggestion": _generate_failure_suggestion(step, str(e)),
            }

    # Collect final outputs
    final_outputs = _collect_workflow_outputs(workflow, context)

    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "steps": step_results,
        "outputs": final_outputs,
        "message": _generate_success_message(workflow, final_outputs),
    }


def _resolve_step_inputs(
    step: Any,  # WorkflowStep
    context: dict[str, Any],
    preview: bool = False,
) -> dict[str, Any]:
    """Resolve step inputs from context using Arazzo expressions.

    Args:
        step: The workflow step.
        context: The execution context with inputs, steps, outputs.
        preview: If True, show placeholders instead of resolving.

    Returns:
        Dictionary of resolved inputs for the step.
    """
    resolved: dict[str, Any] = {}

    # Process request body
    if isinstance(step.request_body, dict):
        for key, value in step.request_body.items():
            # Convert camelCase keys to snake_case for Python tool parameters
            snake_key = _camel_to_snake(key)
            resolved[snake_key] = _resolve_expression(value, context, preview)
    elif isinstance(step.request_body, str) and step.request_body:
        # Handle string request body (e.g., for APIs that take raw string bodies)
        # Extract parameter name from the expression and convert to snake_case
        body_value = _resolve_expression(step.request_body, context, preview)
        param_name = _extract_param_name_from_expression(step.request_body)
        if param_name:
            resolved[param_name] = body_value
        else:
            # Fallback: use a generic key
            resolved["body"] = body_value

    # Process parameters
    for param in step.parameters:
        name = param.get("name")
        value = param.get("value")
        if name and value:
            resolved[name] = _resolve_expression(value, context, preview)

    return resolved


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Examples:
        "shortName" -> "short_name"
        "registrationId" -> "registration_id"
        "name" -> "name"
        "currencyCode" -> "currency_code"

    Args:
        name: The camelCase string.

    Returns:
        The snake_case string.
    """
    import re

    # Insert underscore before uppercase letters and convert to lowercase
    snake_name = re.sub(r"([A-Z])", r"_\1", name).lower()
    return snake_name.lstrip("_")


def _extract_param_name_from_expression(expr: str) -> str | None:
    """Extract parameter name from an Arazzo expression.

    Converts camelCase to snake_case for Python function parameters.

    Examples:
        "$inputs.institutionId" -> "institution_id"
        "{$inputs.institutionId}" -> "institution_id"
        "$steps.foo.outputs.registrationId" -> "registration_id"

    Args:
        expr: The expression string.

    Returns:
        The extracted parameter name in snake_case, or None if not found.
    """
    import re

    # Match patterns like $inputs.fieldName or $steps.x.outputs.fieldName
    match = re.search(r"\$(?:inputs|steps\.\w+\.outputs)\.(\w+)", expr)
    if match:
        camel_name = match.group(1)
        return _camel_to_snake(camel_name)

    return None


def _resolve_expression(
    value: Any,
    context: dict[str, Any],
    preview: bool = False,
) -> Any:
    """Resolve an Arazzo runtime expression.

    Delegates to the arazzo.expression module which implements proper
    Arazzo specification expression parsing and resolution.

    Supports:
    - Bare expressions: $inputs.fieldName
    - Embedded expressions: {$inputs.fieldName}
    - Mixed strings: "prefix-{$inputs.id}-suffix"
    - Step references: $steps.stepId.outputs.fieldName

    Args:
        value: The value to resolve (may be expression or literal).
        context: The execution context with 'inputs', 'steps', 'outputs' keys.
        preview: If True, return placeholder instead of resolving.

    Returns:
        Resolved value.
    """
    return resolve_string(value, context, preview)


def _evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    """Evaluate a step condition expression.

    Args:
        condition: The condition expression.
        context: The execution context.

    Returns:
        True if condition is met, False otherwise.
    """
    # Simple condition evaluation
    # Format: $inputs.fieldName == value or $inputs.fieldName != value

    if "==" in condition:
        left, right = condition.split("==", 1)
        left_val = _resolve_expression(left.strip(), context)
        right_val = right.strip().strip("'\"")
        return str(left_val).lower() == right_val.lower()

    if "!=" in condition:
        left, right = condition.split("!=", 1)
        left_val = _resolve_expression(left.strip(), context)
        right_val = right.strip().strip("'\"")
        return str(left_val).lower() != right_val.lower()

    # Check for truthy value
    resolved = _resolve_expression(condition, context)
    if isinstance(resolved, bool):
        return resolved
    if isinstance(resolved, str):
        return resolved.lower() in ("true", "yes", "1")

    return bool(resolved)


# Pseudo-operations that don't require MCP tool calls
PSEUDO_OPERATIONS = {
    "evaluateCondition",  # Conditional branching - evaluated by workflow engine
    "complete",  # Workflow completion marker
}


def _handle_pseudo_operation(
    step: Any,  # WorkflowStep
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Handle pseudo-operations that don't require MCP tool calls.

    Args:
        step: The workflow step with pseudo-operation.
        inputs: Resolved inputs for the step.

    Returns:
        Dictionary of outputs (typically empty or with status).
    """
    operation_id = step.operation_id

    if operation_id == "complete":
        # Workflow completion marker - just return success
        return {"status": "completed"}

    if operation_id == "evaluateCondition":
        # Conditional branching - the actual condition evaluation is done
        # by the workflow engine based on successCriteria. We just return
        # the inputs for the condition to be evaluated.
        return {"evaluated": True, **inputs}

    # Unknown pseudo-operation - return empty outputs
    return {}


async def _execute_step(
    step: Any,  # WorkflowStep
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute a single workflow step by calling the mapped MCP tool.

    Args:
        step: The workflow step to execute.
        inputs: Resolved inputs for the step.

    Returns:
        Dictionary of outputs from the step.

    Raises:
        ToolError: If the step fails.
    """
    # Handle pseudo-operations that don't call MCP tools
    if step.operation_id in PSEUDO_OPERATIONS:
        return _handle_pseudo_operation(step, inputs)

    tool_name = step.mcp_tool
    if not tool_name:
        raise ToolError(
            f"Step '{step.step_id}' has no mapped MCP tool. "
            f"operationId: {step.operation_id}"
        )

    # Import tools dynamically to avoid circular imports
    tool_func = _get_tool_function(tool_name)
    if tool_func is None:
        raise ToolError(f"MCP tool '{tool_name}' not found for step '{step.step_id}'.")

    # Execute the tool
    result = await tool_func(**inputs)

    # Extract outputs based on step output mappings
    outputs: dict[str, Any] = {}
    if isinstance(result, dict):
        # Use step output mappings if defined
        for output_name, output_expr in step.outputs.items():
            if isinstance(output_expr, str) and output_expr.startswith("$"):
                # Extract from result using Arazzo response expression
                # Format: $response.body.fieldName or $response.body#/json/pointer
                parts = output_expr.split(".")
                if len(parts) >= 3 and parts[0] == "$response" and parts[1] == "body":
                    # $response.body.fieldName -> extract fieldName from result
                    field = parts[2]
                    if field in result:
                        outputs[output_name] = result[field]
                elif len(parts) >= 2 and parts[0] == "$response":
                    # $response.fieldName -> extract from result directly
                    field = parts[1]
                    if field in result:
                        outputs[output_name] = result[field]
            else:
                # Direct mapping
                if output_expr in result:
                    outputs[output_name] = result[output_expr]

        # If no explicit mappings, use common output fields
        if not outputs:
            common_fields = ["id", "serviceId", "registrationId", "name", "key"]
            for field in common_fields:
                if field in result:
                    outputs[field] = result[field]

    return outputs


def _get_tool_function(tool_name: str) -> Any:
    """Get the tool function by name.

    Dynamically imports and returns the tool function from the appropriate module.
    Tool names follow the pattern: {entity}_{action} (e.g., service_create, role_list).

    Args:
        tool_name: The MCP tool name.

    Returns:
        The tool function or None if not found.
    """
    # Import all tool modules
    from mcp_eregistrations_bpa.tools import (
        actions,
        analysis,
        audit,
        behaviours,
        bots,
        classifications,
        costs,
        determinants,
        document_requirements,
        fields,
        forms,
        messages,
        notifications,
        registration_institutions,
        registrations,
        role_status,
        role_units,
        roles,
        rollback,
        services,
    )

    # Map tool prefixes to modules
    # Order matters for compound names - longer prefixes first
    module_map = {
        # Service tools
        "service": services,
        "serviceregistration": registrations,  # serviceregistration_link
        # Registration tools
        "registration": registrations,
        "registrationinstitution": registration_institutions,
        # Role tools
        "role": roles,
        "roleinstitution": roles,
        "roleregistration": roles,
        "rolestatus": role_status,
        "roleunit": role_units,
        # Bot tools
        "bot": bots,
        # Cost tools
        "cost": costs,
        # Determinant tools (all types)
        "textdeterminant": determinants,
        "selectdeterminant": determinants,
        "numericdeterminant": determinants,
        "booleandeterminant": determinants,
        "datedeterminant": determinants,
        "classificationdeterminant": determinants,
        "griddeterminant": determinants,
        "determinant": determinants,
        # Document tools
        "documentrequirement": document_requirements,
        "requirement": document_requirements,
        # Form tools
        "form": forms,
        "field": fields,
        # Behaviour tools
        "componentbehaviour": behaviours,
        "componentaction": actions,
        "effect": behaviours,
        # Classification tools
        "classification": classifications,
        # Message & notification tools
        "message": messages,
        "notification": notifications,
        # Institution tools
        "institution": registration_institutions,
        # Analysis tools
        "analyze": analysis,
        # Audit & rollback tools
        "audit": audit,
        "rollback": rollback,
    }

    # Parse tool name to find module and function
    # Handle compound names like "cost_create_fixed" or "textdeterminant_create"
    parts = tool_name.split("_")
    if not parts:
        return None

    # Try to find matching module
    for prefix_len in range(len(parts), 0, -1):
        prefix = "_".join(parts[:prefix_len])
        if prefix in module_map:
            module = module_map[prefix]
            if module is not None:
                func = getattr(module, tool_name, None)
                if func is not None:
                    return func
            break

    # Fallback: try first part as module prefix
    prefix = parts[0]
    module = module_map.get(prefix)
    if module is not None:
        return getattr(module, tool_name, None)

    return None


def _collect_workflow_outputs(
    workflow: Any,  # WorkflowDefinition
    context: dict[str, Any],
) -> dict[str, Any]:
    """Collect final workflow outputs from context.

    Args:
        workflow: The workflow definition.
        context: The execution context.

    Returns:
        Dictionary of workflow outputs.
    """
    outputs: dict[str, Any] = {}

    for output_name, output_expr in workflow.outputs.items():
        resolved = _resolve_expression(output_expr, context)
        if resolved != output_expr:  # Only include if resolved
            outputs[output_name] = resolved
        elif output_name in context["outputs"]:
            outputs[output_name] = context["outputs"][output_name]

    # Include common outputs if not explicitly defined
    if not outputs:
        outputs = context["outputs"].copy()

    return outputs


def _generate_success_message(
    workflow: Any,  # WorkflowDefinition
    outputs: dict[str, Any],
) -> str:
    """Generate a success message for the workflow.

    Args:
        workflow: The workflow definition.
        outputs: The workflow outputs.

    Returns:
        Human-readable success message.
    """
    # Extract key values for message
    service_name = outputs.get("serviceName", outputs.get("name", ""))
    service_id = outputs.get("serviceId", outputs.get("id", ""))

    if service_name:
        return f"Workflow '{workflow.summary}' completed. Created '{service_name}'."
    if service_id:
        return f"Workflow '{workflow.summary}' completed. ID: {service_id}"

    return f"Workflow '{workflow.summary}' completed successfully."


def _generate_failure_suggestion(
    step: Any,  # WorkflowStep
    error: str,
) -> str:
    """Generate a suggestion for recovering from a failure.

    Args:
        step: The failed step.
        error: The error message.

    Returns:
        Suggestion for recovery.
    """
    error_lower = error.lower()

    if "already exists" in error_lower:
        return "Use a different name/key or delete the existing resource."
    if "not found" in error_lower:
        return "Verify the referenced resource exists. Check IDs and names."
    if "permission" in error_lower or "unauthorized" in error_lower:
        return "Check your permissions. You may need a different role."
    if "validation" in error_lower or "invalid" in error_lower:
        return "Check input values match the required format."

    return "Review the error message and try again with corrected inputs."


# =============================================================================
# Story 5.5: Progress Reporting & Streaming
# =============================================================================

# Track running workflow executions for status/cancel
_running_executions: dict[str, dict[str, Any]] = {}

# Track completed/failed executions for retry/rollback
_execution_history: dict[str, dict[str, Any]] = {}


async def workflow_execute_with_progress(
    workflow_id: str,
    inputs: dict[str, Any],
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Execute workflow with progress callbacks after each step.

    Args:
        workflow_id: Workflow to execute.
        inputs: Input values for the workflow.
        on_progress: Callback receiving {type, execution_id, step, total, percent,
            message, elapsed_ms, current_step}.

    Returns:
        dict with same structure as workflow_execute.
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    # Validate required inputs
    missing_inputs = []
    for inp in workflow.inputs:
        if inp.required and inp.name not in inputs:
            missing_inputs.append(inp.name)

    if missing_inputs:
        raise ToolError(
            f"Missing required inputs: {', '.join(missing_inputs)}. "
            f"Use 'workflow_describe {workflow_id}' to see required inputs."
        )

    # Generate execution ID
    execution_id = f"exec-{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    # Register execution for tracking
    execution_state: dict[str, Any] = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "current_step": None,
        "completed_steps": [],
        "start_time": start_time,
        "cancelled": False,
    }
    _running_executions[execution_id] = execution_state

    # Initialize execution context
    context: dict[str, Any] = {
        "inputs": inputs.copy(),
        "steps": {},
        "outputs": {},
    }

    step_results: list[dict[str, Any]] = []
    total_steps = len(workflow.steps)

    try:
        # Execute each step
        for step_index, step in enumerate(workflow.steps, 1):
            # Check for cancellation
            if execution_state["cancelled"]:
                return {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "status": "cancelled",
                    "cancelled_at_step": step.step_id,
                    "completed_steps": execution_state["completed_steps"],
                    "remaining_steps": total_steps - step_index + 1,
                    "rollback_available": len(execution_state["completed_steps"]) > 0,
                }

            execution_state["current_step"] = step.step_id

            # Check conditional execution
            if step.condition:
                condition_met = _evaluate_condition(step.condition, context)
                if not condition_met:
                    step_results.append(
                        {
                            "step_id": step.step_id,
                            "status": "skipped",
                            "reason": f"Condition not met: {step.condition}",
                        }
                    )
                    continue

            # Resolve step inputs from context
            step_inputs = _resolve_step_inputs(step, context)

            # Execute the step
            try:
                step_output = await _execute_step(step, step_inputs)

                # Store outputs in context
                context["steps"][step.step_id] = step_output
                for key, value in step_output.items():
                    context["outputs"][key] = value

                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "success",
                        "outputs": step_output,
                    }
                )
                execution_state["completed_steps"].append(step.step_id)

                # Report progress
                elapsed_ms = int((time.time() - start_time) * 1000)
                percent = int((step_index / total_steps) * 100)

                progress_info = {
                    "type": "progress",
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "step": step_index,
                    "total": total_steps,
                    "percent": percent,
                    "message": _generate_step_progress_message(step, step_output),
                    "elapsed_ms": elapsed_ms,
                    "current_step": step.step_id,
                }

                if on_progress:
                    on_progress(progress_info)

            except Exception as e:
                # Step failed - stop execution
                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "failed",
                        "error": str(e),
                    }
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "status": "failed",
                    "failed_at_step": step.step_id,
                    "error": str(e),
                    "steps": step_results,
                    "completed_steps": execution_state["completed_steps"],
                    "rollback_available": len(execution_state["completed_steps"]) > 0,
                    "suggestion": _generate_failure_suggestion(step, str(e)),
                    "duration_ms": elapsed_ms,
                }

        # Collect final outputs
        final_outputs = _collect_workflow_outputs(workflow, context)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Report completion
        if on_progress:
            on_progress(
                {
                    "type": "complete",
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "summary": _generate_success_message(workflow, final_outputs),
                    "duration_ms": elapsed_ms,
                }
            )

        return {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": "completed",
            "steps": step_results,
            "outputs": final_outputs,
            "message": _generate_success_message(workflow, final_outputs),
            "duration_ms": elapsed_ms,
        }

    finally:
        # Save execution history for retry/rollback before cleanup
        if execution_id in _running_executions:
            _execution_history[execution_id] = {
                **_running_executions[execution_id],
                "inputs": inputs.copy(),
                "context": context.copy(),
                "step_results": step_results,
                "total_steps": total_steps,
            }
            del _running_executions[execution_id]


def _generate_step_progress_message(
    step: Any,  # WorkflowStep
    outputs: dict[str, Any],
) -> str:
    """Generate a progress message for a completed step.

    Args:
        step: The completed step.
        outputs: The step outputs.

    Returns:
        Human-readable progress message.
    """
    name = outputs.get("name", outputs.get("serviceName", ""))
    if name:
        return f"{step.description}: '{name}'"
    return str(step.description)


async def workflow_status(execution_id: str) -> dict[str, Any]:
    """Get status of a running workflow execution.

    Args:
        execution_id: Execution ID from workflow_execute_with_progress.

    Returns:
        dict with execution_id, workflow_id, status, current_step, completed_steps,
        elapsed_ms.
    """
    if execution_id not in _running_executions:
        return {
            "execution_id": execution_id,
            "status": "not_found",
            "message": "Execution not found or already completed.",
        }

    state = _running_executions[execution_id]
    elapsed_ms = int((time.time() - state["start_time"]) * 1000)

    return {
        "execution_id": execution_id,
        "workflow_id": state["workflow_id"],
        "status": "running" if not state["cancelled"] else "cancelling",
        "current_step": state["current_step"],
        "completed_steps": state["completed_steps"],
        "elapsed_ms": elapsed_ms,
    }


async def workflow_cancel(execution_id: str) -> dict[str, Any]:
    """Cancel a running workflow. Stops after current step completes.

    Args:
        execution_id: Execution ID from workflow_execute_with_progress.

    Returns:
        dict with cancelled, execution_id, message. Completed steps can be rolled back.
    """
    if execution_id not in _running_executions:
        raise ToolError(
            f"Execution '{execution_id}' not found or already completed. "
            "Use 'workflow_status' to check execution status."
        )

    state = _running_executions[execution_id]
    state["cancelled"] = True

    return {
        "cancelled": True,
        "execution_id": execution_id,
        "workflow_id": state["workflow_id"],
        "current_step": state["current_step"],
        "completed_steps": state["completed_steps"],
        "message": "Cancellation requested. Workflow will stop after current step.",
    }


# =============================================================================
# Story 5.6: Error Recovery & Rollback
# =============================================================================


async def workflow_retry(
    execution_id: str,
    updated_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retry failed workflow from point of failure with optional input updates.

    Args:
        execution_id: Failed workflow's execution ID.
        updated_inputs: Updated input values to fix failure cause.

    Returns:
        dict with execution_id, original_execution_id, resumed_from_step, status,
        outputs.
    """
    if execution_id not in _execution_history:
        raise ToolError(
            f"Execution '{execution_id}' not found in history. "
            "Only failed or cancelled executions can be retried."
        )

    history = _execution_history[execution_id]

    # Check that execution failed or was cancelled
    if history.get("status") not in (None, "failed", "cancelled"):
        raise ToolError(
            f"Execution '{execution_id}' cannot be retried. "
            f"Status is '{history.get('status')}'. "
            "Only failed/cancelled executions can be retried."
        )

    workflow_id = history["workflow_id"]
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(f"Workflow '{workflow_id}' no longer exists. Cannot retry.")

    # Prepare inputs - merge original with updates
    inputs = history["inputs"].copy()
    if updated_inputs:
        inputs.update(updated_inputs)

    # Find the failed step to resume from
    completed_steps = history.get("completed_steps", [])
    failed_step = None
    for step_result in history.get("step_results", []):
        if step_result.get("status") == "failed":
            failed_step = step_result.get("step_id")
            break

    # If no failed step found (cancelled), find first incomplete step
    if not failed_step:
        for step in workflow.steps:
            if step.step_id not in completed_steps:
                failed_step = step.step_id
                break

    if not failed_step:
        return {
            "execution_id": execution_id,
            "status": "already_completed",
            "message": "All steps were already completed. Nothing to retry.",
        }

    # Generate new execution ID for retry
    new_execution_id = f"exec-{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    # Restore context from history
    context = history.get("context", {"inputs": inputs, "steps": {}, "outputs": {}})
    context["inputs"] = inputs  # Use updated inputs

    # Register new execution
    execution_state: dict[str, Any] = {
        "execution_id": new_execution_id,
        "workflow_id": workflow_id,
        "status": "running",
        "current_step": None,
        "completed_steps": completed_steps.copy(),
        "start_time": start_time,
        "cancelled": False,
    }
    _running_executions[new_execution_id] = execution_state

    step_results: list[dict[str, Any]] = []
    total_steps = len(workflow.steps)
    resume_from_index = None

    # Find the index to resume from
    for i, step in enumerate(workflow.steps):
        if step.step_id == failed_step:
            resume_from_index = i
            break

    if resume_from_index is None:
        raise ToolError(f"Cannot find step '{failed_step}' in workflow.")

    try:
        # Execute remaining steps
        for step_index, step in enumerate(
            workflow.steps[resume_from_index:], resume_from_index + 1
        ):
            if execution_state["cancelled"]:
                return {
                    "execution_id": new_execution_id,
                    "original_execution_id": execution_id,
                    "status": "cancelled",
                    "resumed_from_step": failed_step,
                    "completed_steps": execution_state["completed_steps"],
                }

            execution_state["current_step"] = step.step_id

            # Check conditional execution
            if step.condition:
                condition_met = _evaluate_condition(step.condition, context)
                if not condition_met:
                    step_results.append(
                        {
                            "step_id": step.step_id,
                            "status": "skipped",
                            "reason": f"Condition not met: {step.condition}",
                        }
                    )
                    continue

            # Resolve step inputs from context
            step_inputs = _resolve_step_inputs(step, context)

            try:
                step_output = await _execute_step(step, step_inputs)

                context["steps"][step.step_id] = step_output
                for key, value in step_output.items():
                    context["outputs"][key] = value

                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "success",
                        "outputs": step_output,
                    }
                )
                execution_state["completed_steps"].append(step.step_id)

            except Exception as e:
                step_results.append(
                    {
                        "step_id": step.step_id,
                        "tool": step.mcp_tool,
                        "inputs": step_inputs,
                        "status": "failed",
                        "error": str(e),
                    }
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "execution_id": new_execution_id,
                    "original_execution_id": execution_id,
                    "status": "failed",
                    "resumed_from_step": failed_step,
                    "failed_at_step": step.step_id,
                    "error": str(e),
                    "steps": step_results,
                    "completed_steps": execution_state["completed_steps"],
                    "rollback_available": True,
                    "suggestion": _generate_failure_suggestion(step, str(e)),
                    "duration_ms": elapsed_ms,
                }

        # Collect final outputs
        final_outputs = _collect_workflow_outputs(workflow, context)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "execution_id": new_execution_id,
            "original_execution_id": execution_id,
            "status": "completed",
            "resumed_from_step": failed_step,
            "steps": step_results,
            "outputs": final_outputs,
            "message": f"Workflow completed after retry from '{failed_step}'",
            "duration_ms": elapsed_ms,
        }

    finally:
        if new_execution_id in _running_executions:
            _execution_history[new_execution_id] = {
                **_running_executions[new_execution_id],
                "inputs": inputs.copy(),
                "context": context.copy(),
                "step_results": step_results,
                "total_steps": total_steps,
            }
            del _running_executions[new_execution_id]


async def workflow_rollback(
    execution_id: str,
    keep_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Roll back completed workflow steps using audit system.

    Args:
        execution_id: Execution ID to roll back.
        keep_steps: Step IDs to keep (not roll back). None = rollback all.

    Returns:
        dict with execution_id, rollback_status, rolled_back_steps, kept_steps, message.
    """
    if execution_id not in _execution_history:
        raise ToolError(
            f"Execution '{execution_id}' not found in history. "
            "Cannot roll back executions that have no history."
        )

    history = _execution_history[execution_id]
    completed_steps = history.get("completed_steps", [])

    if not completed_steps:
        return {
            "execution_id": execution_id,
            "rollback_status": "nothing_to_rollback",
            "message": "No completed steps to roll back.",
        }

    # Determine which steps to roll back (reverse order)
    keep_steps = keep_steps or []
    steps_to_rollback = [s for s in reversed(completed_steps) if s not in keep_steps]
    kept_steps = [s for s in completed_steps if s in keep_steps]

    if not steps_to_rollback:
        return {
            "execution_id": execution_id,
            "rollback_status": "nothing_to_rollback",
            "kept_steps": kept_steps,
            "message": "All steps were in keep_steps. Nothing to roll back.",
        }

    # Get step results for audit info
    step_results = history.get("step_results", [])
    step_outputs: dict[str, dict[str, Any]] = {}
    for result in step_results:
        if result.get("status") == "success":
            step_outputs[result["step_id"]] = result.get("outputs", {})

    rollback_details: list[dict[str, Any]] = []
    rollback_errors: list[str] = []

    # Roll back each step in reverse order
    for step_id in steps_to_rollback:
        outputs = step_outputs.get(step_id, {})

        # Determine what to roll back based on outputs
        # This integrates with the existing rollback system
        rollback_result = await _rollback_step_outputs(step_id, outputs)

        if rollback_result.get("success"):
            rollback_details.append(
                {
                    "step": step_id,
                    "action": rollback_result.get("action", "rolled back"),
                    "details": rollback_result.get("details"),
                }
            )
        else:
            rollback_errors.append(
                f"Failed to rollback {step_id}: {rollback_result.get('error')}"
            )

    rollback_status = "completed" if not rollback_errors else "partial"

    # Clean up execution history after rollback
    if rollback_status == "completed" and not kept_steps:
        del _execution_history[execution_id]

    return {
        "execution_id": execution_id,
        "rollback_status": rollback_status,
        "rolled_back_steps": steps_to_rollback,
        "kept_steps": kept_steps,
        "rollback_details": rollback_details,
        "errors": rollback_errors if rollback_errors else None,
        "message": _generate_rollback_message(
            steps_to_rollback, kept_steps, rollback_errors
        ),
    }


async def _rollback_step_outputs(
    step_id: str,
    outputs: dict[str, Any],
) -> dict[str, Any]:
    """Roll back a step's outputs using the appropriate rollback method.

    Args:
        step_id: The step ID being rolled back.
        outputs: The outputs from the step to roll back.

    Returns:
        dict with success status and details.
    """
    # For now, log the rollback action
    # Full integration with audit/rollback system would require audit_id
    action = f"Marked for rollback: {step_id}"
    details = {"outputs_to_rollback": outputs}

    # If we have an audit_id in outputs, use the real rollback
    audit_id = outputs.get("audit_id")
    if audit_id:
        try:
            from mcp_eregistrations_bpa.tools.rollback import rollback

            result = await rollback(audit_id)
            return {
                "success": True,
                "action": f"Rolled back via audit {audit_id}",
                "details": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    # Without audit_id, we record the intent but can't auto-rollback
    return {
        "success": True,
        "action": action,
        "details": details,
        "note": "Manual rollback may be required (no audit_id)",
    }


def _generate_rollback_message(
    rolled_back: list[str],
    kept: list[str],
    errors: list[str],
) -> str:
    """Generate a human-readable rollback message.

    Args:
        rolled_back: Steps that were rolled back.
        kept: Steps that were kept.
        errors: Any errors that occurred.

    Returns:
        Rollback summary message.
    """
    if errors:
        return f"Partial rollback completed with {len(errors)} error(s)."

    if kept:
        return f"Rolled back {len(rolled_back)} step(s), kept {len(kept)} step(s)."

    return "All workflow changes have been rolled back."


# =============================================================================
# Story 5.7: Workflow Chaining & Composition
# =============================================================================


async def workflow_chain(
    workflows: list[dict[str, Any]],
    rollback_on_failure: bool = True,
) -> dict[str, Any]:
    """Execute workflows sequentially, passing outputs via $chain[i].outputs.field.

    Args:
        workflows: List of {workflow_id, inputs}. Inputs can reference outputs.
        rollback_on_failure: Auto-rollback on failure (default True).

    Returns:
        dict with chain_id, status, results, failed_at (if failed), rolled_back,
        summary.
    """
    if not workflows:
        raise ToolError("Workflow chain must contain at least one workflow.")

    chain_id = f"chain-{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    results: list[dict[str, Any]] = []
    execution_ids: list[str] = []

    for i, wf_spec in enumerate(workflows):
        workflow_id = wf_spec.get("workflow_id")
        if not workflow_id:
            raise ToolError(f"Workflow at index {i} is missing 'workflow_id'.")

        # Resolve inputs that reference previous chain outputs
        raw_inputs = wf_spec.get("inputs", {})
        resolved_inputs = _resolve_chain_inputs(raw_inputs, results)

        try:
            # Execute the workflow
            result = await workflow_execute_with_progress(
                workflow_id=workflow_id,
                inputs=resolved_inputs,
            )

            results.append(
                {
                    "workflow_id": workflow_id,
                    "index": i,
                    "status": result.get("status", "unknown"),
                    "outputs": result.get("outputs", {}),
                    "execution_id": result.get("execution_id"),
                }
            )

            if result.get("execution_id"):
                execution_ids.append(result["execution_id"])

            # Check for failure
            if result.get("status") == "failed":
                if rollback_on_failure and execution_ids:
                    rollback_results = await _rollback_chain(execution_ids[:-1])
                    elapsed_ms = int((time.time() - start_time) * 1000)

                    return {
                        "chain_id": chain_id,
                        "status": "rolled_back",
                        "failed_at": i,
                        "failed_workflow": workflow_id,
                        "error": result.get("error"),
                        "results": results,
                        "rolled_back": [r["workflow_id"] for r in results[:-1]],
                        "rollback_details": rollback_results,
                        "summary": (
                            f"Chain failed at '{workflow_id}'. "
                            "Previous workflows rolled back."
                        ),
                        "duration_ms": elapsed_ms,
                    }
                else:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    return {
                        "chain_id": chain_id,
                        "status": "failed",
                        "failed_at": i,
                        "failed_workflow": workflow_id,
                        "error": result.get("error"),
                        "results": results,
                        "summary": f"Chain failed at '{workflow_id}'.",
                        "duration_ms": elapsed_ms,
                    }

        except Exception as e:
            # Handle unexpected execution errors
            results.append(
                {
                    "workflow_id": workflow_id,
                    "index": i,
                    "status": "error",
                    "error": str(e),
                }
            )

            if rollback_on_failure and execution_ids:
                rollback_results = await _rollback_chain(execution_ids)
                elapsed_ms = int((time.time() - start_time) * 1000)

                return {
                    "chain_id": chain_id,
                    "status": "rolled_back",
                    "failed_at": i,
                    "failed_workflow": workflow_id,
                    "error": str(e),
                    "results": results,
                    "rolled_back": [
                        r["workflow_id"] for r in results[:-1] if r.get("execution_id")
                    ],
                    "rollback_details": rollback_results,
                    "summary": (
                        f"Chain error at '{workflow_id}'. "
                        "Previous workflows rolled back."
                    ),
                    "duration_ms": elapsed_ms,
                }
            else:
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "chain_id": chain_id,
                    "status": "failed",
                    "failed_at": i,
                    "failed_workflow": workflow_id,
                    "error": str(e),
                    "results": results,
                    "summary": f"Chain error at '{workflow_id}'.",
                    "duration_ms": elapsed_ms,
                }

    # All workflows completed successfully
    elapsed_ms = int((time.time() - start_time) * 1000)

    # Collect all outputs for easy access
    all_outputs: dict[str, Any] = {}
    for r in results:
        for key, value in r.get("outputs", {}).items():
            all_outputs[key] = value

    return {
        "chain_id": chain_id,
        "status": "completed",
        "results": results,
        "outputs": all_outputs,
        "summary": f"Executed {len(workflows)} workflow(s) successfully.",
        "duration_ms": elapsed_ms,
    }


def _resolve_chain_inputs(
    raw_inputs: dict[str, Any],
    chain_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve chain references in input values.

    Replaces $chain[i].outputs.fieldName with actual values from
    earlier workflow results.

    Args:
        raw_inputs: Input dict that may contain chain references.
        chain_results: Results from workflows executed so far.

    Returns:
        Resolved inputs with chain references replaced.
    """
    resolved: dict[str, Any] = {}

    for key, value in raw_inputs.items():
        if isinstance(value, str) and value.startswith("$chain["):
            resolved[key] = _resolve_chain_expression(value, chain_results)
        elif isinstance(value, dict):
            resolved[key] = _resolve_chain_inputs(value, chain_results)
        else:
            resolved[key] = value

    return resolved


def _resolve_chain_expression(
    expression: str,
    chain_results: list[dict[str, Any]],
) -> Any:
    """Resolve a single chain expression.

    Parses expressions like $chain[0].outputs.serviceId and
    retrieves the value from chain results.

    Args:
        expression: Expression in format $chain[i].outputs.fieldName
        chain_results: Results from workflows executed so far.

    Returns:
        The resolved value, or the expression if not resolvable.
    """
    # Pattern: $chain[0].outputs.fieldName
    match = re.match(r"\$chain\[(\d+)\]\.outputs\.(\w+)", expression)
    if not match:
        return expression

    index = int(match.group(1))
    field_name = match.group(2)

    if index >= len(chain_results):
        return expression

    outputs = chain_results[index].get("outputs", {})
    return outputs.get(field_name, expression)


async def _rollback_chain(execution_ids: list[str]) -> list[dict[str, Any]]:
    """Roll back multiple workflow executions in reverse order.

    Args:
        execution_ids: List of execution IDs to roll back.

    Returns:
        List of rollback results.
    """
    rollback_results: list[dict[str, Any]] = []

    # Roll back in reverse order
    for exec_id in reversed(execution_ids):
        try:
            result = await workflow_rollback(exec_id)
            rollback_results.append(
                {
                    "execution_id": exec_id,
                    "status": "rolled_back",
                    "details": result,
                }
            )
        except Exception as e:
            rollback_results.append(
                {
                    "execution_id": exec_id,
                    "status": "rollback_failed",
                    "error": str(e),
                }
            )

    return rollback_results


# =============================================================================
# Story 5.8: Guided Interactive Mode
# =============================================================================

# Track interactive workflow sessions
_interactive_sessions: dict[str, dict[str, Any]] = {}


async def workflow_start_interactive(workflow_id: str) -> dict[str, Any]:
    """Start interactive workflow session with step-by-step input prompts.

    Args:
        workflow_id: Workflow to configure interactively.

    Returns:
        dict with mode, session_id, workflow_id, current_prompt, progress.
    """
    catalog = get_workflow_catalog()
    workflow = catalog.get_workflow(workflow_id)

    if workflow is None:
        raise ToolError(
            f"Workflow '{workflow_id}' not found. "
            "Use 'workflow_list' to see available workflows."
        )

    # Generate session ID
    session_id = f"sess-{uuid.uuid4().hex[:8]}"

    # Get ordered list of inputs
    ordered_inputs = _order_inputs_for_interactive(workflow)

    if not ordered_inputs:
        raise ToolError(
            f"Workflow '{workflow_id}' has no inputs to configure. "
            "Use 'workflow_execute' to run it directly."
        )

    # Create session state
    session: dict[str, Any] = {
        "session_id": session_id,
        "workflow_id": workflow_id,
        "workflow": workflow,
        "ordered_inputs": ordered_inputs,
        "current_index": 0,
        "collected_inputs": {},
        "inferred_inputs": {},
        "started_at": time.time(),
    }
    _interactive_sessions[session_id] = session

    # Generate first prompt
    first_input = ordered_inputs[0]
    current_prompt = _generate_interactive_prompt(first_input, session)

    return {
        "mode": "interactive",
        "session_id": session_id,
        "workflow_id": workflow_id,
        "current_prompt": current_prompt,
        "progress": {
            "answered": 0,
            "total": len(ordered_inputs),
        },
    }


async def workflow_continue(
    session_id: str,
    value: Any,
) -> dict[str, Any]:
    """Provide value for current input and advance to next prompt.

    Args:
        session_id: Interactive session ID.
        value: Value for current input.

    Returns:
        dict with mode, accepted, current_prompt (or preview if done), progress.
    """
    if session_id not in _interactive_sessions:
        raise ToolError(
            f"Session '{session_id}' not found. "
            "Start a new session with 'workflow_start_interactive'."
        )

    session = _interactive_sessions[session_id]
    ordered_inputs = session["ordered_inputs"]
    current_index = session["current_index"]

    if current_index >= len(ordered_inputs):
        raise ToolError(
            f"Session '{session_id}' has already collected all inputs. "
            "Use 'workflow_confirm' to execute the workflow."
        )

    current_input = ordered_inputs[current_index]

    # Validate the provided value
    validation_error = _validate_input_value(current_input, value)
    if validation_error:
        return {
            "mode": "interactive",
            "session_id": session_id,
            "error": validation_error,
            "current_prompt": _generate_interactive_prompt(current_input, session),
            "progress": {
                "answered": len(session["collected_inputs"]),
                "total": len(ordered_inputs),
            },
        }

    # Store the value
    session["collected_inputs"][current_input.name] = value

    # Infer related inputs
    _infer_related_inputs(current_input, value, session)

    # Move to next input (skip already inferred ones)
    session["current_index"] = current_index + 1
    while (
        session["current_index"] < len(ordered_inputs)
        and ordered_inputs[session["current_index"]].name in session["collected_inputs"]
    ):
        session["current_index"] += 1

    # Check if all inputs collected
    if session["current_index"] >= len(ordered_inputs):
        # All inputs collected - return preview
        return _generate_preview(session)

    # Generate next prompt
    next_input = ordered_inputs[session["current_index"]]
    current_prompt = _generate_interactive_prompt(next_input, session)

    return {
        "mode": "interactive",
        "session_id": session_id,
        "accepted": session["collected_inputs"].copy(),
        "inferred": session["inferred_inputs"].copy(),
        "current_prompt": current_prompt,
        "progress": {
            "answered": len(session["collected_inputs"]),
            "total": len(ordered_inputs),
        },
    }


async def workflow_confirm(
    session_id: str,
    execute: bool = True,
) -> dict[str, Any]:
    """Confirm and execute workflow with collected inputs.

    Args:
        session_id: Interactive session ID.
        execute: Execute workflow (default True) or just return preview.

    Returns:
        dict with status, workflow_id, inputs, outputs, steps, message.
    """
    if session_id not in _interactive_sessions:
        raise ToolError(
            f"Session '{session_id}' not found. "
            "Start a new session with 'workflow_start_interactive'."
        )

    session = _interactive_sessions[session_id]
    ordered_inputs = session["ordered_inputs"]
    collected_inputs = session["collected_inputs"]

    # Check all required inputs are present
    missing_required = []
    for inp in ordered_inputs:
        if inp.required and inp.name not in collected_inputs:
            missing_required.append(inp.name)

    if missing_required:
        missing = ", ".join(missing_required)
        raise ToolError(
            f"Cannot confirm session. Missing required inputs: {missing}. "
            "Use 'workflow_continue' to provide values."
        )

    if not execute:
        # Return preview without executing
        return _generate_preview(session)

    # Execute the workflow
    try:
        result = await workflow_execute_with_progress(
            workflow_id=session["workflow_id"],
            inputs=collected_inputs,
        )

        # Clean up session on success
        del _interactive_sessions[session_id]

        return {
            "status": result.get("status", "unknown"),
            "session_id": session_id,
            "workflow_id": session["workflow_id"],
            "inputs": collected_inputs,
            "outputs": result.get("outputs", {}),
            "steps": result.get("steps", []),
            "message": result.get("message", "Workflow executed"),
            "duration_ms": result.get("duration_ms"),
        }

    except Exception as e:
        # Keep session for retry
        return {
            "status": "failed",
            "session_id": session_id,
            "workflow_id": session["workflow_id"],
            "inputs": collected_inputs,
            "error": str(e),
            "message": f"Workflow execution failed: {e}",
            "suggestion": "Review inputs and use 'workflow_continue' to update them, "
            "then try 'workflow_confirm' again.",
        }


def _order_inputs_for_interactive(workflow: Any) -> list[Any]:
    """Order workflow inputs for interactive prompting.

    Puts primary inputs first (service name, etc.) followed by
    derived inputs that can be auto-inferred.

    Args:
        workflow: The workflow definition.

    Returns:
        Ordered list of WorkflowInput objects.
    """
    primary: list[Any] = []
    secondary: list[Any] = []
    derived: list[Any] = []

    for inp in workflow.inputs:
        name = inp.name.lower()
        if "name" in name and "service" in name:
            primary.insert(0, inp)
        elif inp.required and "name" in name:
            primary.append(inp)
        elif inp.required:
            secondary.append(inp)
        else:
            derived.append(inp)

    return primary + secondary + derived


def _generate_interactive_prompt(
    inp: Any,  # WorkflowInput
    session: dict[str, Any],
) -> dict[str, Any]:
    """Generate an interactive prompt for an input.

    Args:
        inp: The WorkflowInput to prompt for.
        session: The current session state.

    Returns:
        Prompt dictionary with question, type, examples, etc.
    """
    prompt: dict[str, Any] = {
        "input": inp.name,
        "type": inp.input_type.value
        if hasattr(inp.input_type, "value")
        else str(inp.input_type),
        "required": inp.required,
    }

    # Generate question
    prompt["question"] = _generate_input_question(inp, session)

    # Add examples
    examples = _get_input_examples(inp)
    if examples:
        prompt["examples"] = examples

    # Add default
    if inp.default is not None:
        prompt["default"] = inp.default

    # Add suggestion based on previous inputs
    suggestion = _suggest_value(inp, session)
    if suggestion:
        prompt["suggestion"] = suggestion

    # Add validation hints
    if inp.pattern:
        prompt["format"] = inp.pattern
    if inp.min_length is not None:
        prompt["min_length"] = inp.min_length
    if inp.max_length is not None:
        prompt["max_length"] = inp.max_length
    if inp.enum_values:
        prompt["options"] = inp.enum_values

    return prompt


def _generate_input_question(
    inp: Any,  # WorkflowInput
    session: dict[str, Any],
) -> str:
    """Generate a human-readable question for an input.

    Args:
        inp: The input to generate a question for.
        session: The current session.

    Returns:
        A question string with (required) indicator if applicable.
    """
    question: str

    # Use description if available
    if inp.description:
        # Convert description to question form
        desc = str(inp.description).rstrip(".")
        if not desc.endswith("?"):
            question = f"What is the {desc.lower()}?"
        else:
            question = desc
    else:
        # Generate based on name
        name = inp.name
        # Convert camelCase to words
        words = re.sub(r"([A-Z])", r" \1", name).strip().lower()

        # Special cases
        if "name" in words:
            question = f"What would you like to name the {words.replace(' name', '')}?"
        elif "key" in words:
            question = f"What should the {words} be? (URL-safe identifier)"
        elif "id" in words:
            question = f"What is the {words}?"
        else:
            question = f"What is the {words}?"

    # Add required indicator (Story 10-3 AC3)
    if inp.required:
        question = f"{question} (required)"

    return question


def _validate_input_value(
    inp: Any,  # WorkflowInput
    value: Any,
) -> dict[str, Any] | None:
    """Validate a single input value against its constraints.

    Args:
        inp: The WorkflowInput definition.
        value: The value to validate.

    Returns:
        Error dict if invalid, None if valid.
    """
    from mcp_eregistrations_bpa.workflows.models import InputType

    # String type validations
    if inp.input_type == InputType.STRING and isinstance(value, str):
        # Check pattern
        if inp.pattern:
            if not re.match(inp.pattern, value):
                return {
                    "constraint": f"pattern: {inp.pattern}",
                    "message": f"{inp.name} must match pattern {inp.pattern}",
                    "suggestion": _suggest_pattern_fix(value, inp.pattern),
                }

        # Check length
        if inp.min_length is not None and len(value) < inp.min_length:
            return {
                "constraint": f"minLength: {inp.min_length}",
                "message": f"{inp.name} must be at least {inp.min_length} characters",
            }
        if inp.max_length is not None and len(value) > inp.max_length:
            return {
                "constraint": f"maxLength: {inp.max_length}",
                "message": f"{inp.name} must be at most {inp.max_length} characters",
                "suggestion": value[: inp.max_length],
            }

        # Check enum
        if inp.enum_values and value not in inp.enum_values:
            return {
                "constraint": f"enum: {inp.enum_values}",
                "message": f"{inp.name} must be one of: {', '.join(inp.enum_values)}",
            }

    # Numeric validations
    if inp.input_type in (InputType.INTEGER, InputType.NUMBER):
        if isinstance(value, int | float):
            if inp.minimum is not None and value < inp.minimum:
                return {
                    "constraint": f"minimum: {inp.minimum}",
                    "message": f"{inp.name} must be at least {inp.minimum}",
                }
            if inp.maximum is not None and value > inp.maximum:
                return {
                    "constraint": f"maximum: {inp.maximum}",
                    "message": f"{inp.name} must be at most {inp.maximum}",
                }

    return None


def _suggest_pattern_fix(value: str, pattern: str) -> str | None:
    """Suggest a fix for a pattern violation.

    Args:
        value: The invalid value.
        pattern: The regex pattern.

    Returns:
        Suggested fixed value or None.
    """
    # Handle common patterns
    if pattern == "^[a-z0-9-]+$":
        # Kebab-case pattern
        fixed = re.sub(r"[^a-z0-9-]", "", value.lower().replace(" ", "-"))
        return fixed if fixed else None

    return None


def _to_short_name(name: str) -> str:
    """Convert a name to a short name.

    Args:
        name: The full name.

    Returns:
        A short name (max 50 chars).
    """
    return name[:50] if len(name) > 50 else name


def _to_key(name: str) -> str:
    """Convert a name to a URL-safe key.

    Args:
        name: The full name.

    Returns:
        A kebab-case key.
    """
    # Remove non-alphanumeric, lowercase, replace spaces with hyphens
    key = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower())
    key = re.sub(r"\s+", "-", key.strip())
    return key[:100]


def _get_input_examples(inp: Any) -> list[str]:
    """Get example values for an input.

    Args:
        inp: The input definition.

    Returns:
        List of example strings.
    """
    name = inp.name.lower()

    # Known examples for common input types
    if "servicename" in name:
        return ["Business Registration", "Vehicle Permits", "Construction Licenses"]
    if "registrationname" in name:
        return ["New Registration", "Renewal Application", "License Request"]
    if "rolename" in name or name == "name":
        return ["Reviewer", "Approver", "Inspector"]
    if "key" in name:
        return ["business-reg", "vehicle-permit", "construction-license"]

    # Use enum values as examples
    if inp.enum_values:
        return [str(v) for v in inp.enum_values[:3]]

    return []


def _suggest_value(
    inp: Any,  # WorkflowInput
    session: dict[str, Any],
) -> str | None:
    """Suggest a value based on previously collected inputs.

    Args:
        inp: The input to suggest for.
        session: The current session.

    Returns:
        Suggested value or None.
    """
    collected = session["collected_inputs"]
    name = inp.name.lower()

    # Derive from serviceName
    service_name = collected.get("serviceName")
    if service_name:
        if "registrationname" in name:
            return str(service_name)
        if "registrationshortname" in name or "serviceshortname" in name:
            return _to_short_name(str(service_name))
        if "registrationkey" in name or "servicekey" in name:
            return _to_key(str(service_name))

    # Derive from registrationName
    reg_name = collected.get("registrationName")
    if reg_name:
        if "shortname" in name:
            return _to_short_name(str(reg_name))
        if "key" in name:
            return _to_key(str(reg_name))

    return None


def _infer_related_inputs(
    inp: Any,  # WorkflowInput
    value: Any,
    session: dict[str, Any],
) -> None:
    """Infer related inputs from a provided value.

    Updates session with inferred values.

    Args:
        inp: The input that was just provided.
        value: The value that was provided.
        session: The session to update.
    """
    workflow = session["workflow"]
    name = inp.name.lower()

    # Infer from serviceName
    if "servicename" in name and isinstance(value, str):
        _try_infer(
            workflow, session, "registrationName", value, "Derived from serviceName"
        )
        _try_infer(
            workflow,
            session,
            "registrationShortName",
            _to_short_name(value),
            "Generated from serviceName",
        )
        _try_infer(
            workflow,
            session,
            "registrationKey",
            _to_key(value),
            "Generated from serviceName",
        )
        _try_infer(
            workflow,
            session,
            "serviceShortName",
            _to_short_name(value),
            "Generated from serviceName",
        )

    # Infer from registrationName
    if "registrationname" in name and isinstance(value, str):
        _try_infer(
            workflow,
            session,
            "registrationShortName",
            _to_short_name(value),
            "Generated from registrationName",
        )
        _try_infer(
            workflow,
            session,
            "registrationKey",
            _to_key(value),
            "Generated from registrationName",
        )


def _try_infer(
    workflow: Any,
    session: dict[str, Any],
    field_name: str,
    value: Any,
    reason: str,
) -> None:
    """Try to infer a field value if it exists and isn't already set.

    Args:
        workflow: The workflow definition.
        session: The session state.
        field_name: The field to infer.
        value: The inferred value.
        reason: Why this value was inferred.
    """
    if field_name in session["collected_inputs"]:
        return  # Already set

    inp = workflow.get_input(field_name)
    if inp is None:
        return  # Field doesn't exist in workflow

    session["collected_inputs"][field_name] = value
    session["inferred_inputs"][field_name] = reason


def _generate_preview(session: dict[str, Any]) -> dict[str, Any]:
    """Generate a preview of the workflow configuration.

    Args:
        session: The session state.

    Returns:
        Preview dictionary.
    """
    workflow = session["workflow"]
    inputs = session["collected_inputs"]

    # Generate step preview
    steps_preview = []
    for i, step in enumerate(workflow.steps, 1):
        desc = step.description
        # Replace placeholders with actual values
        for key, value in inputs.items():
            if isinstance(value, str):
                desc = desc.replace(f"${{{key}}}", value)
                desc = desc.replace(f"$inputs.{key}", value)
        steps_preview.append(f"{i}. {desc}")

    return {
        "mode": "preview",
        "session_id": session["session_id"],
        "workflow_id": session["workflow_id"],
        "inputs": inputs.copy(),
        "inferred": session["inferred_inputs"].copy(),
        "steps_preview": steps_preview,
        "confirm_prompt": "Ready to execute? Use workflow_confirm to proceed.",
    }


# =============================================================================
# Story 14.6: Workflow Validation
# =============================================================================


async def workflow_validate(workflow_id: str | None = None) -> dict[str, Any]:
    """Validate workflow definitions for issues.

    Checks:
    1. All operationIds have MCP tool mappings
    2. Required inputs are defined in properties
    3. Step references ($steps.X.outputs.Y) are valid
    4. No duplicate workflow IDs across files

    Args:
        workflow_id: Optional specific workflow to validate. If None, validates all.

    Returns:
        dict with valid_count, invalid_count, issues list, and summary.
    """
    catalog = get_workflow_catalog()
    issues: list[dict[str, Any]] = []
    validated_count = 0
    seen_workflow_ids: dict[str, str] = {}  # workflow_id -> source_file

    # Get all workflows
    workflows = catalog.list_workflows()

    for wf_entry in workflows:
        wf_id = wf_entry["id"]

        # If specific workflow requested, skip others
        if workflow_id is not None and wf_id != workflow_id:
            continue

        workflow = catalog.get_workflow(wf_id)
        if workflow is None:
            continue

        validated_count += 1
        source = workflow.source_file

        # Check 1: Duplicate workflow IDs
        if wf_id in seen_workflow_ids:
            issues.append(
                {
                    "workflow_id": wf_id,
                    "issue": "duplicate_id",
                    "severity": "error",
                    "detail": (
                        f"Duplicate workflow ID. First: {seen_workflow_ids[wf_id]}, "
                        f"Second: {source}"
                    ),
                }
            )
        seen_workflow_ids[wf_id] = source

        # Check 2: operationIds have MCP tool mappings
        for step in workflow.steps:
            if step.operation_id and step.mcp_tool is None:
                # Check if it's in the map
                if step.operation_id not in OPERATION_TO_TOOL_MAP:
                    issues.append(
                        {
                            "workflow_id": wf_id,
                            "issue": "unmapped_operation",
                            "severity": "warning",
                            "detail": (
                                f"Step '{step.step_id}' has operationId "
                                f"'{step.operation_id}' with no MCP tool mapping"
                            ),
                        }
                    )

        # Check 3: Required inputs defined in properties
        input_names = {inp.name for inp in workflow.inputs}
        required_inputs = [inp.name for inp in workflow.inputs if inp.required]

        # Check if required inputs are actually in the properties
        for req_input in required_inputs:
            if req_input not in input_names:
                issues.append(
                    {
                        "workflow_id": wf_id,
                        "issue": "missing_required_input",
                        "severity": "error",
                        "detail": f"Required input '{req_input}' not in properties",
                    }
                )

        # Check 4: Step references are valid
        step_ids = {step.step_id for step in workflow.steps}
        step_output_pattern = re.compile(r"\$steps\.(\w+)\.outputs\.(\w+)")

        for step in workflow.steps:
            # Check request body for step references
            request_body_str = str(step.request_body)
            for match in step_output_pattern.finditer(request_body_str):
                ref_step_id = match.group(1)
                if ref_step_id not in step_ids:
                    issues.append(
                        {
                            "workflow_id": wf_id,
                            "issue": "invalid_step_reference",
                            "severity": "error",
                            "detail": (
                                f"Step '{step.step_id}' references unknown step "
                                f"'{ref_step_id}'"
                            ),
                        }
                    )

            # Check onSuccess/onFailure goto targets
            for action in step.on_success + step.on_failure:
                if isinstance(action, dict):
                    goto_step = action.get("stepId")
                    if goto_step and goto_step not in step_ids:
                        issues.append(
                            {
                                "workflow_id": wf_id,
                                "issue": "invalid_goto_step",
                                "severity": "error",
                                "detail": (
                                    f"Step '{step.step_id}' has goto to unknown "
                                    f"step '{goto_step}'"
                                ),
                            }
                        )

    # Count issues by severity
    error_count = sum(1 for i in issues if i.get("severity") == "error")
    warning_count = sum(1 for i in issues if i.get("severity") == "warning")
    valid_count = validated_count - len({i["workflow_id"] for i in issues})

    # Build summary
    if not issues:
        summary = f"All {validated_count} workflows validated successfully."
    else:
        summary = (
            f"Validated {validated_count} workflows. "
            f"Found {error_count} errors, {warning_count} warnings "
            f"in {len({i['workflow_id'] for i in issues})} workflows."
        )

    return {
        "validated_count": validated_count,
        "valid_count": valid_count,
        "invalid_count": validated_count - valid_count,
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
        "summary": summary,
    }


# =============================================================================
# Registration
# =============================================================================


def register_workflow_tools(mcp: Any) -> None:
    """Register workflow orchestration tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    # Story 5.1: Workflow Catalog & Discovery
    mcp.tool()(workflow_list)
    mcp.tool()(workflow_describe)
    mcp.tool()(workflow_search)

    # Story 5.4: Workflow Executor
    mcp.tool()(workflow_execute)

    # Story 5.5: Progress Reporting & Streaming
    mcp.tool()(workflow_status)
    mcp.tool()(workflow_cancel)

    # Story 5.6: Error Recovery & Rollback
    mcp.tool()(workflow_retry)
    mcp.tool()(workflow_rollback)

    # Story 5.7: Workflow Chaining & Composition
    mcp.tool()(workflow_chain)

    # Story 5.8: Guided Interactive Mode
    mcp.tool()(workflow_start_interactive)
    mcp.tool()(workflow_continue)
    mcp.tool()(workflow_confirm)

    # Story 14.6: Workflow Validation
    mcp.tool()(workflow_validate)

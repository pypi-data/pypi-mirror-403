"""Service debugger tools for BPA configuration issues.

This module provides MCP tools for detecting, investigating, and fixing
orphaned references and configuration issues in BPA services.

The workflow is collaborative:
1. debug_scan - Scan for issues, group by type
2. debug_investigate - Investigate root cause of specific issue
3. debug_fix - Execute fix after user approval

Write operations follow the audit-before-write pattern.

API Endpoint used:
- POST /service/{service_id}/recover-orphan-config - Scan for issues
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
from mcp_eregistrations_bpa.tools.debug_strategies import (
    get_fix_summary,
    get_issue_info,
    group_issues_by_severity,
    group_issues_by_type,
    prioritize_issues,
)
from mcp_eregistrations_bpa.tools.large_response import large_response_handler

__all__ = [
    "debug_scan",
    "debug_investigate",
    "debug_fix",
    "debug_fix_batch",
    "debug_group_issues",
    "debug_plan",
    "debug_verify",
    "register_debug_tools",
]


@large_response_handler(
    navigation={
        "list_issues": "jq '.all_issues'",
        "by_severity": "jq '.by_severity'",
        "high_severity": "jq '.all_issues[] | select(.severity == \"high\")'",
        "by_type": "jq '.by_type'",
        "batch_fixable": "jq '.by_type[] | select(.batch_fixable == true)'",
    }
)
async def debug_scan(service_id: str | int) -> dict[str, Any]:
    """Scan service for configuration issues and orphaned references.

    Calls BPA debug endpoint and returns grouped issues with fix recommendations.
    Large responses (>100KB) are saved to file with navigation hints.

    Args:
        service_id: BPA service UUID.

    Returns:
        dict with service_id, total_issues, by_severity, by_type, summary,
        prioritized_issues.
    """
    if not service_id:
        raise ToolError(
            "Cannot scan service: 'service_id' is required. "
            "Use 'service_list' to find valid IDs."
        )

    issues_list: list[dict[str, Any]] = []
    try:
        async with BPAClient() as client:
            try:
                # Call the debug endpoint - returns a list of issues
                response = await client.post(
                    "/service/{service_id}/recover-orphan-config",
                    path_params={"service_id": service_id},
                    json={},
                    resource_type="debug",
                )
                # Response is a list wrapped in dict or direct list
                if isinstance(response, list):
                    issues_list = response
                elif isinstance(response, dict) and "issues" in response:
                    issues_list = response["issues"]
            except BPANotFoundError:
                raise ToolError(
                    f"Service '{service_id}' not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=str(service_id))

    # Group and analyze issues
    by_type = group_issues_by_type(issues_list)
    by_severity = group_issues_by_severity(issues_list)
    summary = get_fix_summary(issues_list)
    prioritized = prioritize_issues(issues_list)

    # Build type breakdown with fix info
    type_details: list[dict[str, Any]] = []
    for obj_type, type_issues in by_type.items():
        info = get_issue_info(obj_type)
        type_details.append(
            {
                "type": obj_type,
                "count": len(type_issues),
                "severity": info.severity.value if info else "unknown",
                "fix_strategy": info.fix_strategy.value if info else "manual_review",
                "batch_fixable": info.batch_fixable if info else False,
                "fix_tool": info.fix_tool if info else None,
                "sample_issue": type_issues[0] if type_issues else None,
            }
        )

    # Sort by count descending
    type_details.sort(key=lambda x: int(x["count"]), reverse=True)

    return {
        "service_id": str(service_id),
        "total_issues": len(issues_list),
        "by_severity": {
            "high": len(by_severity["high"]),
            "medium": len(by_severity["medium"]),
            "low": len(by_severity["low"]),
            "unknown": len(by_severity["unknown"]),
        },
        "by_type": type_details,
        "summary": summary,
        "prioritized_issues": prioritized[:20],  # Return top 20 for context
        "all_issues": issues_list,  # Full list for batch operations
    }


async def debug_investigate(
    service_id: str | int,
    issue: dict[str, Any],
) -> dict[str, Any]:
    """Investigate root cause of a specific configuration issue.

    Fetches context using existing tools to determine why the issue exists
    and what fix options are available.

    Args:
        service_id: BPA service UUID.
        issue: Issue dict from debug_scan (needs objectType, componentKey, etc.).

    Returns:
        dict with issue, root_cause, context, fix_options, recommended_fix.
    """
    if not service_id:
        raise ToolError("'service_id' is required.")
    if not issue:
        raise ToolError("'issue' dict is required (from debug_scan).")

    object_type = issue.get("objectType", "unknown")
    component_key = issue.get("componentKey")
    parent_id = issue.get("parentId")
    conflicting_value = issue.get("conflictingValue")

    info = get_issue_info(object_type)
    if not info:
        return {
            "issue": issue,
            "root_cause": f"Unknown issue type: {object_type}",
            "context": None,
            "fix_options": [
                {
                    "id": "manual",
                    "description": "Manual review required - unknown issue type",
                    "confidence": "low",
                    "action": None,
                }
            ],
            "recommended_fix": "manual",
        }

    context: dict[str, Any] = {}
    root_cause = ""
    fix_options: list[dict[str, Any]] = []

    try:
        async with BPAClient() as client:
            # Investigation depends on issue type
            if object_type == "effects_determinant":
                # Behaviour references non-existent determinant
                root_cause = (
                    f"Component '{component_key}' has a behaviour that references "
                    f"determinant '{conflicting_value}' which no longer exists."
                )

                # Try to get the behaviour
                if component_key:
                    try:
                        behaviour = await client.get(
                            "/service/{service_id}/componentactions/{component_key}",
                            path_params={
                                "service_id": service_id,
                                "component_key": component_key,
                            },
                            resource_type="behaviour",
                        )
                        context["behaviour"] = behaviour
                    except BPAClientError:
                        context["behaviour"] = "Could not fetch behaviour details"

                fix_options = [
                    {
                        "id": "delete_effect",
                        "description": (
                            f"Delete the behaviour/effect from component "
                            f"'{component_key}'"
                        ),
                        "confidence": "high",
                        "action": {
                            "tool": "effect_delete",
                            "params": {"behaviour_id": parent_id},
                        },
                    },
                ]

            elif object_type == "determinant":
                # Orphaned determinant
                root_cause = (
                    f"Determinant '{conflicting_value}' references a field or "
                    "component that no longer exists."
                )

                # Try to get determinant details
                if conflicting_value:
                    try:
                        det = await client.get(
                            "/determinant/{id}",
                            path_params={"id": conflicting_value},
                            resource_type="determinant",
                            resource_id=conflicting_value,
                        )
                        context["determinant"] = det
                    except BPAClientError:
                        context["determinant"] = "Could not fetch determinant details"

                fix_options = [
                    {
                        "id": "delete_determinant",
                        "description": (
                            f"Delete orphaned determinant '{conflicting_value}'"
                        ),
                        "confidence": "high",
                        "action": {
                            "tool": "determinant_delete",
                            "params": {
                                "service_id": service_id,
                                "determinant_id": conflicting_value,
                            },
                        },
                    },
                ]

            elif object_type == "missing_determinants_in_component_behaviours":
                # Behaviour with empty determinant list
                root_cause = (
                    f"Component '{component_key}' has a behaviour with no determinants "
                    "- it will never trigger."
                )

                fix_options = [
                    {
                        "id": "delete_behaviour",
                        "description": (
                            f"Delete the empty behaviour from component "
                            f"'{component_key}'"
                        ),
                        "confidence": "high",
                        "action": {
                            "tool": "effect_delete",
                            "params": {"behaviour_id": parent_id},
                        },
                    },
                ]

            elif object_type == "catalog":
                # Component references non-existent catalog
                root_cause = (
                    f"Component '{component_key}' references catalog "
                    f"'{conflicting_value}' which does not exist."
                )

                fix_options = [
                    {
                        "id": "clear_catalog",
                        "description": (
                            f"Clear catalog reference from component '{component_key}'"
                        ),
                        "confidence": "medium",
                        "action": {
                            "tool": "form_component_update",
                            "params": {
                                "service_id": service_id,
                                "component_key": component_key,
                                "updates": {
                                    "data": {"dataSrc": "values", "values": []},
                                },
                            },
                        },
                    },
                    {
                        "id": "manual_reassign",
                        "description": "Manually assign a different catalog",
                        "confidence": "low",
                        "action": None,
                    },
                ]

            elif object_type in (
                "translation_moustache",
                "component_content_moustache",
                "component_html_moustache",
                "component_label_missing_moustache",
                "message_moustache",
            ):
                # Template references missing field
                root_cause = (
                    f"Template in '{issue.get('parentName', 'unknown')}' uses "
                    f"variable '{{{{conflicting_value}}}}' which references a "
                    f"field that no longer exists."
                )

                fix_options = [
                    {
                        "id": "manual_review",
                        "description": (
                            "Review and update the template to remove or fix "
                            "the reference"
                        ),
                        "confidence": "medium",
                        "action": None,
                    },
                ]

            else:
                # Default for other types
                root_cause = issue.get("message", f"Configuration issue: {object_type}")
                fix_options = [
                    {
                        "id": "manual_review",
                        "description": f"Manual review required for {object_type}",
                        "confidence": "low",
                        "action": None,
                    },
                ]

    except BPAClientError as e:
        context["error"] = str(e)

    # Determine recommended fix
    recommended = (
        fix_options[0]["id"]
        if fix_options and fix_options[0].get("confidence") in ("high", "medium")
        else "manual_review"
    )

    return {
        "issue": issue,
        "issue_type_info": info.to_dict() if info else None,
        "root_cause": root_cause,
        "context": context,
        "fix_options": fix_options,
        "recommended_fix": recommended,
    }


async def debug_fix(
    service_id: str | int,
    issue: dict[str, Any],
    fix_option: str,
) -> dict[str, Any]:
    """Execute a fix for a configuration issue. Audited write operation.

    This tool executes the specified fix using existing MCP tools.
    Audit trail is created for rollback support.

    Args:
        service_id: BPA service UUID.
        issue: Issue dict from debug_scan.
        fix_option: Fix option ID from debug_investigate (e.g., "delete_effect").

    Returns:
        dict with success, issue, fix_applied, result, audit_id.
    """
    if not service_id:
        raise ToolError("'service_id' is required.")
    if not issue:
        raise ToolError("'issue' dict is required (from debug_scan).")
    if not fix_option:
        raise ToolError("'fix_option' is required (from debug_investigate).")

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    object_type = issue.get("objectType", "unknown")
    component_key = issue.get("componentKey")
    parent_id = issue.get("parentId")
    conflicting_value = issue.get("conflictingValue")

    audit_logger = AuditLogger()

    # Create audit record
    audit_id = await audit_logger.record_pending(
        user_email=user_email,
        operation_type="debug_fix",
        object_type=f"debug_{object_type}",
        object_id=parent_id or conflicting_value or component_key,
        params={
            "service_id": str(service_id),
            "issue": issue,
            "fix_option": fix_option,
        },
    )

    try:
        async with BPAClient() as client:
            result: dict[str, Any] = {}

            if fix_option == "delete_effect" and parent_id:
                # Delete the behaviour/effect
                await client.delete(
                    "/componentbehaviour/{behaviour_id}",
                    path_params={"behaviour_id": parent_id},
                    resource_type="behaviour",
                    resource_id=parent_id,
                )
                result = {
                    "action": "deleted_behaviour",
                    "behaviour_id": parent_id,
                    "component_key": component_key,
                }

            elif fix_option == "delete_determinant" and conflicting_value:
                # Delete the orphaned determinant
                await client.delete(
                    "/service/{service_id}/determinant/{determinant_id}",
                    path_params={
                        "service_id": service_id,
                        "determinant_id": conflicting_value,
                    },
                    resource_type="determinant",
                    resource_id=conflicting_value,
                )
                result = {
                    "action": "deleted_determinant",
                    "determinant_id": conflicting_value,
                }

            elif fix_option == "delete_behaviour" and parent_id:
                # Same as delete_effect
                await client.delete(
                    "/componentbehaviour/{behaviour_id}",
                    path_params={"behaviour_id": parent_id},
                    resource_type="behaviour",
                    resource_id=parent_id,
                )
                result = {
                    "action": "deleted_behaviour",
                    "behaviour_id": parent_id,
                    "component_key": component_key,
                }

            elif fix_option == "clear_catalog" and component_key:
                # Clear catalog reference from form component
                # Get current component and update to clear dataSrc
                try:
                    comp = await client.get(
                        "/service/{service_id}/form/{form_type}/component/{component_key}",
                        path_params={
                            "service_id": service_id,
                            "form_type": "applicant",
                            "component_key": component_key,
                        },
                    )
                    # Prepare update to clear catalog reference
                    updates = {
                        "dataSrc": "",
                        "data": {"values": []},
                    }
                    await client.put(
                        "/service/{service_id}/form/{form_type}/component/{component_key}",
                        path_params={
                            "service_id": service_id,
                            "form_type": "applicant",
                            "component_key": component_key,
                        },
                        json=updates,
                    )
                    result = {
                        "action": "cleared_catalog",
                        "component_key": component_key,
                        "previous_dataSrc": comp.get("dataSrc"),
                    }
                except BPAClientError:
                    # Fallback to guidance if direct update fails
                    result = {
                        "action": "manual_required",
                        "message": (
                            f"Use form_component_update to clear catalog from "
                            f"'{component_key}'"
                        ),
                    }

            elif fix_option == "remove_translation":
                # Sync translations to clean up orphaned references
                try:
                    await client.put(
                        "/translations/sync",
                        json={},
                    )
                    result = {
                        "action": "synced_translations",
                        "message": (
                            "Translation sync completed. Orphaned references may be "
                            "cleaned. Re-scan to verify."
                        ),
                        "component_key": component_key,
                        "conflicting_value": conflicting_value,
                    }
                except BPAClientError:
                    # Sync not available, provide guidance
                    result = {
                        "action": "manual_required",
                        "message": (
                            f"Translation sync unavailable. Manually edit translation "
                            f"to remove reference to '{conflicting_value}'"
                        ),
                        "component_key": component_key,
                    }

            else:
                await audit_logger.mark_failed(
                    audit_id=audit_id,
                    error_message=f"Unknown fix option: {fix_option}",
                )
                raise ToolError(
                    f"Unknown or unsupported fix option: {fix_option}. "
                    "Use debug_investigate to get valid fix options."
                )

            # Mark audit as success
            await audit_logger.mark_success(audit_id=audit_id, result=result)

            return {
                "success": True,
                "issue": issue,
                "fix_applied": fix_option,
                "result": result,
                "audit_id": audit_id,
            }

    except ToolError:
        raise
    except BPAClientError as e:
        await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
        raise translate_error(e, resource_type="debug_fix", resource_id=str(service_id))


async def debug_group_issues(
    service_id: str | int,
    issues: list[dict[str, Any]],
    group_by: str = "type",
) -> dict[str, Any]:
    """Group configuration issues by specified criteria.

    Read-only analysis tool - does not call BPA API.

    Args:
        service_id: BPA service UUID (for context).
        issues: Issue list from debug_scan.
        group_by: type, severity, parent, fix_strategy, or batch_fixable.

    Returns:
        dict with service_id, group_by, groups (list with name, count, issues,
        sample_issue, aggregate_impact), total_groups.
    """
    valid_group_by = {"type", "severity", "parent", "fix_strategy", "batch_fixable"}
    if group_by not in valid_group_by:
        valid_opts = ", ".join(sorted(valid_group_by))
        raise ToolError(f"Invalid group_by '{group_by}'. Must be one of: {valid_opts}")

    if not issues:
        return {
            "service_id": str(service_id),
            "group_by": group_by,
            "groups": [],
            "total_groups": 0,
        }

    # Group issues based on criterion
    grouped: dict[str, list[dict[str, Any]]] = {}

    if group_by == "type":
        grouped = group_issues_by_type(issues)

    elif group_by == "severity":
        by_severity = group_issues_by_severity(issues)
        # Filter out empty severity groups
        grouped = {k: v for k, v in by_severity.items() if v}

    elif group_by == "parent":
        for issue in issues:
            parent_id = issue.get("parentId", "unknown")
            parent_name = issue.get("parentName", "unknown")
            if parent_id != "unknown":
                key = f"{parent_name} ({parent_id})"
            else:
                key = parent_name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(issue)

    elif group_by == "fix_strategy":
        for issue in issues:
            obj_type = issue.get("objectType", "unknown")
            info = get_issue_info(obj_type)
            strategy = info.fix_strategy.value if info else "manual_review"
            if strategy not in grouped:
                grouped[strategy] = []
            grouped[strategy].append(issue)

    elif group_by == "batch_fixable":
        grouped = {"batch_fixable": [], "manual_required": []}
        for issue in issues:
            obj_type = issue.get("objectType", "unknown")
            info = get_issue_info(obj_type)
            if info and info.batch_fixable:
                grouped["batch_fixable"].append(issue)
            else:
                grouped["manual_required"].append(issue)
        # Filter out empty groups
        grouped = {k: v for k, v in grouped.items() if v}

    # Build groups with aggregate impact
    groups: list[dict[str, Any]] = []
    for name, group_issues in grouped.items():
        # Calculate aggregate impact
        severity_breakdown: dict[str, int] = {
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        }
        batch_fixable_count = 0
        manual_count = 0
        fix_strategies: set[str] = set()

        for issue in group_issues:
            obj_type = issue.get("objectType", "unknown")
            info = get_issue_info(obj_type)
            if info:
                severity_breakdown[info.severity.value] += 1
                if info.batch_fixable:
                    batch_fixable_count += 1
                else:
                    manual_count += 1
                fix_strategies.add(info.fix_strategy.value)
            else:
                severity_breakdown["unknown"] += 1
                manual_count += 1

        # Filter out zero-count severities
        filtered_severity = {k: v for k, v in severity_breakdown.items() if v > 0}

        groups.append(
            {
                "name": name,
                "count": len(group_issues),
                "issues": group_issues,
                "sample_issue": group_issues[0] if group_issues else None,
                "aggregate_impact": {
                    "severity_breakdown": filtered_severity,
                    "batch_fixable_count": batch_fixable_count,
                    "manual_count": manual_count,
                    "fix_strategies": sorted(fix_strategies),
                },
            }
        )

    # Sort groups by priority: high severity batch-fixable first
    def group_priority(g: dict[str, Any]) -> tuple[int, int, int]:
        impact = g["aggregate_impact"]
        high_count = impact["severity_breakdown"].get("high", 0)
        batch_count = impact["batch_fixable_count"]
        total = g["count"]
        # Higher high severity = lower priority number (comes first)
        # Higher batch fixable = lower priority number (comes first)
        return (-high_count, -batch_count, -total)

    groups.sort(key=group_priority)

    return {
        "service_id": str(service_id),
        "group_by": group_by,
        "groups": groups,
        "total_groups": len(groups),
    }


async def debug_fix_batch(
    service_id: str | int,
    issues: list[dict[str, Any]],
    fix_option: str,
) -> dict[str, Any]:
    """Execute fixes for multiple issues in a batch. Audited write operation.

    Executes fixes sequentially with single audit trail. Stops on first
    failure and returns rollback info for completed fixes.

    Args:
        service_id: BPA service UUID.
        issues: List of issue dicts from debug_scan.
        fix_option: Fix option ID (e.g., "delete_effect", "delete_determinant").

    Returns:
        dict with success, total, success_count, failed_count, results,
        failed_at (if failed), rollback_info, audit_id.
    """
    if not service_id:
        raise ToolError("'service_id' is required.")
    if not fix_option:
        raise ToolError("'fix_option' is required.")

    # Handle empty issues list
    if not issues:
        return {
            "success": True,
            "total": 0,
            "success_count": 0,
            "failed_count": 0,
            "results": [],
            "failed_at": None,
            "rollback_info": None,
            "audit_id": None,
        }

    # Get authenticated user for audit
    try:
        user_email = get_current_user_email()
    except NotAuthenticatedError as e:
        raise ToolError(str(e))

    audit_logger = AuditLogger()

    # Create single audit record for the batch
    audit_id = await audit_logger.record_pending(
        user_email=user_email,
        operation_type="debug_fix_batch",
        object_type="debug_batch",
        object_id=str(service_id),
        params={
            "service_id": str(service_id),
            "fix_option": fix_option,
            "issue_count": len(issues),
        },
    )

    results: list[dict[str, Any]] = []
    success_count = 0
    failed_count = 0
    failed_at: int | None = None

    try:
        async with BPAClient() as client:
            for idx, issue in enumerate(issues):
                object_type = issue.get("objectType", "unknown")
                component_key = issue.get("componentKey")
                parent_id = issue.get("parentId")
                conflicting_value = issue.get("conflictingValue")

                try:
                    result: dict[str, Any] = {}

                    if fix_option == "delete_effect" and parent_id:
                        await client.delete(
                            "/componentbehaviour/{behaviour_id}",
                            path_params={"behaviour_id": parent_id},
                            resource_type="behaviour",
                            resource_id=parent_id,
                        )
                        result = {
                            "action": "deleted_behaviour",
                            "behaviour_id": parent_id,
                            "component_key": component_key,
                        }

                    elif fix_option == "delete_determinant" and conflicting_value:
                        await client.delete(
                            "/service/{service_id}/determinant/{determinant_id}",
                            path_params={
                                "service_id": service_id,
                                "determinant_id": conflicting_value,
                            },
                            resource_type="determinant",
                            resource_id=conflicting_value,
                        )
                        result = {
                            "action": "deleted_determinant",
                            "determinant_id": conflicting_value,
                        }

                    elif fix_option == "delete_behaviour" and parent_id:
                        await client.delete(
                            "/componentbehaviour/{behaviour_id}",
                            path_params={"behaviour_id": parent_id},
                            resource_type="behaviour",
                            resource_id=parent_id,
                        )
                        result = {
                            "action": "deleted_behaviour",
                            "behaviour_id": parent_id,
                            "component_key": component_key,
                        }

                    else:
                        # Unsupported fix option for this issue
                        raise ToolError(
                            f"Fix option '{fix_option}' not applicable for "
                            f"issue type '{object_type}'"
                        )

                    # Success for this issue
                    results.append(
                        {
                            "index": idx,
                            "issue": issue,
                            "success": True,
                            "result": result,
                        }
                    )
                    success_count += 1

                except (BPAClientError, ToolError) as e:
                    # Failure - stop batch execution
                    failed_count = 1
                    failed_at = idx
                    results.append(
                        {
                            "index": idx,
                            "issue": issue,
                            "success": False,
                            "error": str(e),
                        }
                    )
                    break

    except BPAClientError as e:
        # Connection-level failure
        await audit_logger.mark_failed(audit_id=audit_id, error_message=str(e))
        raise translate_error(
            e, resource_type="debug_fix_batch", resource_id=str(service_id)
        )

    # Determine overall success
    overall_success = failed_at is None

    # Build rollback info
    rollback_info = None
    if success_count > 0:
        rollback_info = {
            "audit_id": audit_id,
            "completed_count": success_count,
            "can_rollback": True,
        }

    # Mark audit based on outcome
    if overall_success:
        await audit_logger.mark_success(
            audit_id=audit_id,
            result={
                "total": len(issues),
                "success_count": success_count,
                "results": results,
            },
        )
    else:
        await audit_logger.mark_failed(
            audit_id=audit_id,
            error_message=f"Batch failed at index {failed_at}",
        )

    return {
        "success": overall_success,
        "total": len(issues),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
        "failed_at": failed_at,
        "rollback_info": rollback_info,
        "audit_id": audit_id,
    }


# Phase ordering for fix dependencies
# Effects reference determinants, so delete effects first
PHASE_ORDER = [
    ("delete_effect", "Delete Orphaned Effects"),
    ("delete_behaviour", "Delete Empty Behaviours"),
    ("delete_determinant", "Delete Orphaned Determinants"),
    ("clear_catalog_reference", "Clear Catalog References"),
    ("remove_translation", "Fix Translation References"),
    ("manual_review", "Manual Review Required"),
]


async def debug_plan(service_id: str | int) -> dict[str, Any]:
    """Generate a fix plan for all issues in a service.

    Performs full scan and generates ordered phases respecting dependencies.
    Effects must be fixed before orphaned determinants.

    Args:
        service_id: BPA service UUID.

    Returns:
        dict with service_id, total_issues, phases (ordered list with phase_id,
        name, description, fix_strategy, issues, batch_fixable, approval_required,
        estimated_impact), summary.
    """
    if not service_id:
        raise ToolError(
            "Cannot generate plan: 'service_id' is required. "
            "Use 'service_list' to find valid IDs."
        )

    # Perform the scan
    scan_result = await debug_scan(service_id)
    all_issues = scan_result.get("all_issues", [])

    if not all_issues:
        return {
            "service_id": str(service_id),
            "total_issues": 0,
            "phases": [],
            "summary": {
                "total_phases": 0,
                "batch_fixable_count": 0,
                "manual_count": 0,
                "estimated_time": "No issues to fix",
            },
        }

    # Group issues by fix strategy
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for issue in all_issues:
        obj_type = issue.get("objectType", "unknown")
        info = get_issue_info(obj_type)
        strategy = info.fix_strategy.value if info else "manual_review"
        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append(issue)

    # Build phases in dependency order
    phases: list[dict[str, Any]] = []
    phase_num = 1
    total_batch_fixable = 0
    total_manual = 0

    for strategy, phase_name in PHASE_ORDER:
        if strategy not in by_strategy:
            continue

        phase_issues = by_strategy[strategy]
        if not phase_issues:
            continue

        # Calculate phase metadata
        batch_fixable = all(
            (info := get_issue_info(i.get("objectType", ""))) and info.batch_fixable
            for i in phase_issues
        )

        # Get affected components
        affected_components: set[str] = set()
        for issue in phase_issues:
            comp_key = issue.get("componentKey")
            if comp_key:
                affected_components.add(comp_key)

        # Determine severity (highest in phase)
        severity_priority = {"high": 0, "medium": 1, "low": 2}
        phase_severity = "low"
        for issue in phase_issues:
            info = get_issue_info(issue.get("objectType", ""))
            if info and severity_priority.get(
                info.severity.value, 3
            ) < severity_priority.get(phase_severity, 3):
                phase_severity = info.severity.value

        # Build phase description
        sample_issue = phase_issues[0]
        obj_type = sample_issue.get("objectType", "unknown")
        info = get_issue_info(obj_type)
        description = info.description if info else f"Fix {obj_type} issues"

        phase = {
            "phase_id": f"phase-{phase_num}",
            "name": phase_name,
            "description": description,
            "fix_strategy": strategy,
            "issues": phase_issues,
            "issue_count": len(phase_issues),
            "batch_fixable": batch_fixable,
            "approval_required": True,  # All phases need approval
            "estimated_impact": {
                "affected_components": sorted(affected_components)[:10],
                "total_affected": len(affected_components),
                "severity": phase_severity,
            },
        }

        phases.append(phase)
        phase_num += 1

        if batch_fixable:
            total_batch_fixable += len(phase_issues)
        else:
            total_manual += len(phase_issues)

    # Add any remaining strategies not in PHASE_ORDER
    for strategy, phase_issues in by_strategy.items():
        if any(strategy == s for s, _ in PHASE_ORDER):
            continue  # Already processed
        if not phase_issues:
            continue

        phases.append(
            {
                "phase_id": f"phase-{phase_num}",
                "name": f"Fix {strategy.replace('_', ' ').title()}",
                "description": f"Resolve issues using {strategy} strategy",
                "fix_strategy": strategy,
                "issues": phase_issues,
                "issue_count": len(phase_issues),
                "batch_fixable": False,
                "approval_required": True,
                "estimated_impact": {
                    "affected_components": [],
                    "total_affected": 0,
                    "severity": "unknown",
                },
            }
        )
        total_manual += len(phase_issues)
        phase_num += 1

    # Generate summary
    summary = {
        "total_phases": len(phases),
        "batch_fixable_count": total_batch_fixable,
        "manual_count": total_manual,
        "phase_order": [p["phase_id"] for p in phases],
        "estimated_workflow": (
            f"{len(phases)} approval steps: "
            f"{total_batch_fixable} auto-fixable, "
            f"{total_manual} require manual review"
        ),
    }

    return {
        "service_id": str(service_id),
        "total_issues": len(all_issues),
        "phases": phases,
        "summary": summary,
    }


def _issue_key(issue: dict[str, Any]) -> str:
    """Create unique key for an issue for comparison."""
    obj_type = issue.get("objectType", "")
    parent_id = issue.get("parentId", "")
    component_key = issue.get("componentKey", "")
    conflicting_value = issue.get("conflictingValue", "")
    return f"{obj_type}:{parent_id}:{component_key}:{conflicting_value}"


async def debug_verify(
    service_id: str | int,
    fix_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify fixes were applied successfully by rescanning service.

    Compares current state with previous state (from fix_result) if provided.

    Args:
        service_id: BPA service UUID.
        fix_result: Optional result from debug_fix or debug_fix_batch.

    Returns:
        dict with service_id, current_issues, total_current, verification
        (resolved_count, remaining_count, new_count, improvement_percentage),
        status (verified|partial|failed|baseline).
    """
    if not service_id:
        raise ToolError(
            "Cannot verify: 'service_id' is required. "
            "Use 'service_list' to find valid IDs."
        )

    # Perform fresh scan
    scan_result = await debug_scan(service_id)
    current_issues = scan_result.get("all_issues", [])
    total_current = len(current_issues)

    # Build current issue set for comparison
    current_keys = {_issue_key(issue) for issue in current_issues}

    # If no fix_result provided, return baseline status
    if not fix_result:
        return {
            "service_id": str(service_id),
            "current_issues": scan_result,
            "total_current": total_current,
            "verification": {
                "resolved_count": 0,
                "remaining_count": total_current,
                "new_count": 0,
                "improvement_percentage": 0.0,
                "comparison_available": False,
            },
            "status": "baseline",
            "summary": f"Baseline scan: {total_current} issues found",
        }

    # Extract previous issues from fix_result
    # Handle both debug_fix (single) and debug_fix_batch (batch) results
    previous_issues: list[dict[str, Any]] = []

    if "issue" in fix_result:
        # Single fix result
        previous_issues = [fix_result["issue"]]
    elif "results" in fix_result:
        # Batch fix result - extract issues from results
        for result in fix_result.get("results", []):
            if "issue" in result:
                previous_issues.append(result["issue"])

    # If no previous issues found, we can still compare with total
    previous_keys = {_issue_key(issue) for issue in previous_issues}
    total_previous = (
        len(previous_issues) if previous_issues else fix_result.get("total", 0)
    )

    # Calculate verification metrics
    resolved_keys = previous_keys - current_keys
    remaining_keys = previous_keys & current_keys
    new_keys = current_keys - previous_keys

    resolved_count = len(resolved_keys)
    remaining_count = len(remaining_keys)
    new_count = len(new_keys)

    # Calculate improvement percentage
    if total_previous > 0:
        improvement = (resolved_count / total_previous) * 100
    else:
        improvement = 100.0 if total_current == 0 else 0.0

    # Determine status
    if resolved_count > 0 and remaining_count == 0 and new_count == 0:
        status = "verified"
        summary = f"All {resolved_count} targeted issues resolved successfully"
    elif resolved_count > 0:
        status = "partial"
        summary = (
            f"Resolved {resolved_count} of {total_previous} issues "
            f"({improvement:.1f}% improvement)"
        )
        if new_count > 0:
            summary += f", but {new_count} new issues detected"
    elif new_count > 0:
        status = "failed"
        summary = f"No issues resolved, {new_count} new issues detected"
    else:
        status = "failed"
        summary = "No improvement detected"

    return {
        "service_id": str(service_id),
        "current_issues": scan_result,
        "total_current": total_current,
        "verification": {
            "resolved_count": resolved_count,
            "remaining_count": remaining_count,
            "new_count": new_count,
            "improvement_percentage": round(improvement, 1),
            "comparison_available": True,
            "previous_total": total_previous,
        },
        "status": status,
        "summary": summary,
    }


def register_debug_tools(mcp: Any) -> None:
    """Register debug tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(debug_scan)
    mcp.tool()(debug_investigate)
    mcp.tool()(debug_fix)
    mcp.tool()(debug_fix_batch)
    mcp.tool()(debug_group_issues)
    mcp.tool()(debug_plan)
    mcp.tool()(debug_verify)

"""Issue type definitions and fix strategies for BPA service debugger.

This module defines the known issue types returned by the BPA debug endpoint,
their severity levels, and strategies for investigating and fixing them.

The debug endpoint (POST /service/{id}/recover-orphan-config) returns issues
that reference orphaned or invalid configuration elements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

# Type alias for issue dicts
IssueDict = dict[str, Any]
IssueList = list[IssueDict]

__all__ = [
    "Severity",
    "IssueTypeInfo",
    "FixStrategy",
    "ISSUE_TYPES",
    "get_issue_info",
    "group_issues_by_type",
    "group_issues_by_severity",
    "prioritize_issues",
]


class Severity(str, Enum):
    """Issue severity levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FixStrategy(str, Enum):
    """Available fix strategies."""

    DELETE_EFFECT = "delete_effect"
    DELETE_DETERMINANT = "delete_determinant"
    DELETE_BEHAVIOUR = "delete_behaviour"
    CLEAR_CATALOG_REFERENCE = "clear_catalog_reference"
    REMOVE_TRANSLATION = "remove_translation"
    CLEAR_COPY_VALUE = "clear_copy_value"
    REMOVE_DUPLICATE = "remove_duplicate"
    FIX_ROLE_REGISTRATION = "fix_role_registration"
    MANUAL_REVIEW = "manual_review"


@dataclass
class IssueTypeInfo:
    """Information about an issue type."""

    name: str
    description: str
    severity: Severity
    fix_strategy: FixStrategy
    investigation_tool: str | None
    fix_tool: str | None
    requires_user_input: bool = False
    batch_fixable: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "fix_strategy": self.fix_strategy.value,
            "investigation_tool": self.investigation_tool,
            "fix_tool": self.fix_tool,
            "requires_user_input": self.requires_user_input,
            "batch_fixable": self.batch_fixable,
        }


# Issue type definitions based on BPA debug endpoint response
ISSUE_TYPES: dict[str, IssueTypeInfo] = {
    # HIGH SEVERITY - Break service functionality
    "effects_determinant": IssueTypeInfo(
        name="effects_determinant",
        description="Component behaviour references a non-existent determinant",
        severity=Severity.HIGH,
        fix_strategy=FixStrategy.DELETE_EFFECT,
        investigation_tool="componentbehaviour_get_by_component",
        fix_tool="effect_delete",
        requires_user_input=False,
        batch_fixable=True,
    ),
    "determinant": IssueTypeInfo(
        name="determinant",
        description="Orphaned determinant with invalid field references",
        severity=Severity.HIGH,
        fix_strategy=FixStrategy.DELETE_DETERMINANT,
        investigation_tool="determinant_get",
        fix_tool="determinant_delete",
        requires_user_input=False,
        batch_fixable=True,
    ),
    # MEDIUM SEVERITY - May cause display or logic issues
    "missing_determinants_in_component_behaviours": IssueTypeInfo(
        name="missing_determinants_in_component_behaviours",
        description="Component behaviour has empty determinant list",
        severity=Severity.MEDIUM,
        fix_strategy=FixStrategy.DELETE_BEHAVIOUR,
        investigation_tool="componentbehaviour_get_by_component",
        fix_tool="effect_delete",
        requires_user_input=False,
        batch_fixable=True,
    ),
    "translation_moustache": IssueTypeInfo(
        name="translation_moustache",
        description="Translation references non-existent form field",
        severity=Severity.MEDIUM,
        fix_strategy=FixStrategy.REMOVE_TRANSLATION,
        investigation_tool=None,
        fix_tool="debug_fix",  # Uses /translations/sync
        requires_user_input=False,
        batch_fixable=True,  # Translation sync can be batch-applied
    ),
    "catalog": IssueTypeInfo(
        name="catalog",
        description="Component references non-existent catalog",
        severity=Severity.MEDIUM,
        fix_strategy=FixStrategy.CLEAR_CATALOG_REFERENCE,
        investigation_tool="form_component_get",
        fix_tool="debug_fix",  # Uses clear_catalog to clear dataSrc
        requires_user_input=False,  # Auto-clears invalid reference
        batch_fixable=True,
    ),
    # LOW SEVERITY - Minor display or configuration issues
    "component_content_moustache": IssueTypeInfo(
        name="component_content_moustache",
        description="Content block references missing form field",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.MANUAL_REVIEW,
        investigation_tool="form_component_get",
        fix_tool="form_component_update",
        requires_user_input=True,
        batch_fixable=False,
    ),
    "component_html_moustache": IssueTypeInfo(
        name="component_html_moustache",
        description="HTML component references missing form field",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.MANUAL_REVIEW,
        investigation_tool="form_component_get",
        fix_tool="form_component_update",
        requires_user_input=True,
        batch_fixable=False,
    ),
    "component_label_missing_moustache": IssueTypeInfo(
        name="component_label_missing_moustache",
        description="Component label references missing variable",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.MANUAL_REVIEW,
        investigation_tool="form_component_get",
        fix_tool="form_component_update",
        requires_user_input=True,
        batch_fixable=False,
    ),
    "component_linking_requirement_orphan_reference": IssueTypeInfo(
        name="component_linking_requirement_orphan_reference",
        description="Requirement link references non-existent component",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.MANUAL_REVIEW,
        investigation_tool="documentrequirement_list",
        fix_tool="documentrequirement_update",
        requires_user_input=True,
        batch_fixable=False,
    ),
    "copyValueFrom": IssueTypeInfo(
        name="copyValueFrom",
        description="Copy-value action references non-existent field",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.CLEAR_COPY_VALUE,
        investigation_tool="form_component_get",
        fix_tool="form_component_update",
        requires_user_input=False,
        batch_fixable=True,
    ),
    "duplicate_component_on_form": IssueTypeInfo(
        name="duplicate_component_on_form",
        description="Duplicate component keys detected on form",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.REMOVE_DUPLICATE,
        investigation_tool="form_get",
        fix_tool="form_component_remove",
        requires_user_input=True,  # Need to choose which to keep
        batch_fixable=False,
    ),
    "message_moustache": IssueTypeInfo(
        name="message_moustache",
        description="Message template references missing form field",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.MANUAL_REVIEW,
        investigation_tool="message_get",
        fix_tool="message_update",
        requires_user_input=True,
        batch_fixable=False,
    ),
    "role_registration_missing": IssueTypeInfo(
        name="role_registration_missing",
        description="Role references non-existent registration",
        severity=Severity.LOW,
        fix_strategy=FixStrategy.FIX_ROLE_REGISTRATION,
        investigation_tool="role_get",
        fix_tool="role_update",
        requires_user_input=True,  # Need to select correct registration
        batch_fixable=False,
    ),
}


def get_issue_info(object_type: str) -> IssueTypeInfo | None:
    """Get information about an issue type.

    Args:
        object_type: The objectType value from BPA debug response.

    Returns:
        IssueTypeInfo if known, None otherwise.
    """
    return ISSUE_TYPES.get(object_type)


def group_issues_by_type(issues: IssueList) -> dict[str, IssueList]:
    """Group issues by their objectType.

    Args:
        issues: List of issue dicts from BPA debug endpoint.

    Returns:
        Dict mapping objectType to list of issues.
    """
    grouped: dict[str, IssueList] = {}
    for issue in issues:
        obj_type = issue.get("objectType", "unknown")
        if obj_type not in grouped:
            grouped[obj_type] = []
        grouped[obj_type].append(issue)
    return grouped


def group_issues_by_severity(issues: IssueList) -> dict[str, IssueList]:
    """Group issues by severity level.

    Args:
        issues: List of issue dicts from BPA debug endpoint.

    Returns:
        Dict mapping severity to list of issues.
    """
    grouped: dict[str, IssueList] = {"high": [], "medium": [], "low": [], "unknown": []}
    for issue in issues:
        obj_type = issue.get("objectType", "unknown")
        info = get_issue_info(obj_type)
        if info:
            grouped[info.severity.value].append(issue)
        else:
            grouped["unknown"].append(issue)
    return grouped


def prioritize_issues(issues: IssueList) -> IssueList:
    """Sort issues by fix priority.

    Priority order:
    1. High severity, batch-fixable first (effects_determinant, determinant)
    2. Medium severity, batch-fixable
    3. High severity, requires user input
    4. Medium severity, requires user input
    5. Low severity

    Args:
        issues: List of issue dicts from BPA debug endpoint.

    Returns:
        Sorted list of issues.
    """
    severity_order: dict[str, int] = {"high": 0, "medium": 1, "low": 2, "unknown": 3}

    def sort_key(issue: IssueDict) -> tuple[int, int, str]:
        obj_type = issue.get("objectType", "unknown")
        info = get_issue_info(obj_type)
        if info:
            severity_rank = severity_order.get(info.severity.value, 3)
            # Batch-fixable items come first within same severity
            batch_rank = 0 if info.batch_fixable else 1
        else:
            severity_rank = 3
            batch_rank = 1
        return (severity_rank, batch_rank, obj_type)

    return sorted(issues, key=sort_key)


def get_fix_summary(issues: IssueList) -> dict[str, Any]:
    """Generate a summary of issues for user approval.

    Args:
        issues: List of issue dicts from BPA debug endpoint.

    Returns:
        Summary dict with counts, severity breakdown, and recommended actions.
    """
    by_type = group_issues_by_type(issues)
    by_severity = group_issues_by_severity(issues)

    # Count batch-fixable vs manual
    batch_fixable_count = 0
    manual_count = 0
    for issue in issues:
        info = get_issue_info(issue.get("objectType", ""))
        if info and info.batch_fixable:
            batch_fixable_count += 1
        else:
            manual_count += 1

    type_summary: list[dict[str, Any]] = []
    for obj_type, type_issues in by_type.items():
        info = get_issue_info(obj_type)
        type_summary.append(
            {
                "type": obj_type,
                "count": len(type_issues),
                "severity": info.severity.value if info else "unknown",
                "fix_strategy": info.fix_strategy.value if info else "manual_review",
                "batch_fixable": info.batch_fixable if info else False,
            }
        )

    # Sort by count descending
    type_summary.sort(key=lambda x: int(x["count"]), reverse=True)

    return {
        "total_issues": len(issues),
        "by_severity": {
            "high": len(by_severity["high"]),
            "medium": len(by_severity["medium"]),
            "low": len(by_severity["low"]),
            "unknown": len(by_severity["unknown"]),
        },
        "batch_fixable": batch_fixable_count,
        "requires_manual": manual_count,
        "by_type": type_summary,
    }

"""MCP tools for BPA operations.

This module provides tools for interacting with the BPA API through MCP.
"""

from mcp_eregistrations_bpa.tools.actions import (
    componentaction_get,
    componentaction_get_by_component,
    register_action_tools,
)
from mcp_eregistrations_bpa.tools.analysis import (
    analyze_service,
    register_analysis_tools,
)
from mcp_eregistrations_bpa.tools.audit import (
    audit_get,
    audit_list,
    register_audit_tools,
)
from mcp_eregistrations_bpa.tools.behaviours import (
    componentbehaviour_get,
    componentbehaviour_get_by_component,
    componentbehaviour_list,
    effect_create,
    effect_delete,
    register_behaviour_tools,
)
from mcp_eregistrations_bpa.tools.bots import (
    bot_create,
    bot_delete,
    bot_get,
    bot_list,
    bot_update,
    bot_upgrade_version,
    bot_validate,
    register_bot_tools,
)
from mcp_eregistrations_bpa.tools.classifications import (
    classification_create,
    classification_export_csv,
    classification_get,
    classification_list,
    classification_update,
    register_classification_tools,
)
from mcp_eregistrations_bpa.tools.costs import (
    cost_create_fixed,
    cost_create_formula,
    cost_delete,
    cost_update,
    register_cost_tools,
)
from mcp_eregistrations_bpa.tools.debugger import (
    debug_fix,
    debug_fix_batch,
    debug_group_issues,
    debug_investigate,
    debug_plan,
    debug_scan,
    debug_verify,
    register_debug_tools,
)
from mcp_eregistrations_bpa.tools.determinants import (
    booleandeterminant_create,
    classificationdeterminant_create,
    datedeterminant_create,
    determinant_delete,
    determinant_get,
    determinant_list,
    determinant_search,
    griddeterminant_create,
    numericdeterminant_create,
    register_determinant_tools,
    selectdeterminant_create,
    textdeterminant_create,
    textdeterminant_update,
)
from mcp_eregistrations_bpa.tools.document_requirements import (
    documentrequirement_create,
    documentrequirement_delete,
    documentrequirement_list,
    documentrequirement_update,
    register_document_requirement_tools,
    requirement_list,
)
from mcp_eregistrations_bpa.tools.export import (
    register_export_tools,
    service_copy,
    service_export_raw,
    service_to_yaml,
)
from mcp_eregistrations_bpa.tools.external_services import (
    muleservice_get,
    muleservice_list,
    register_external_service_tools,
)
from mcp_eregistrations_bpa.tools.fields import (
    field_get,
    field_list,
    register_field_tools,
)
from mcp_eregistrations_bpa.tools.formio_helpers import (
    build_checkbox,
    build_columns,
    build_number,
    build_panel,
    build_select,
    build_textarea,
    build_textfield,
)
from mcp_eregistrations_bpa.tools.forms import (
    form_component_add,
    form_component_get,
    form_component_move,
    form_component_remove,
    form_component_update,
    form_get,
    form_update,
    register_form_tools,
)
from mcp_eregistrations_bpa.tools.messages import (
    message_create,
    message_delete,
    message_get,
    message_list,
    message_update,
    register_message_tools,
)
from mcp_eregistrations_bpa.tools.notifications import (
    notification_create,
    notification_list,
    register_notification_tools,
)
from mcp_eregistrations_bpa.tools.registration_institutions import (
    institution_create,
    institution_discover,
    register_registration_institution_tools,
    registrationinstitution_create,
    registrationinstitution_delete,
    registrationinstitution_get,
    registrationinstitution_list,
    registrationinstitution_list_by_institution,
)
from mcp_eregistrations_bpa.tools.registrations import (
    register_registration_tools,
    registration_activate,
    registration_create,
    registration_delete,
    registration_get,
    registration_list,
    serviceregistration_link,
)
from mcp_eregistrations_bpa.tools.role_status import (
    register_role_status_tools,
    rolestatus_create,
    rolestatus_delete,
    rolestatus_get,
    rolestatus_update,
)
from mcp_eregistrations_bpa.tools.role_units import (
    register_role_unit_tools,
    roleunit_create,
    roleunit_delete,
    roleunit_get,
    roleunit_list,
)
from mcp_eregistrations_bpa.tools.roles import (
    register_role_tools,
    role_create,
    role_delete,
    role_get,
    role_list,
    role_update,
    roleinstitution_create,
    roleregistration_create,
)
from mcp_eregistrations_bpa.tools.rollback import (
    register_rollback_tools,
    rollback,
    rollback_cleanup,
    rollback_history,
)
from mcp_eregistrations_bpa.tools.services import (
    register_service_tools,
    service_activate,
    service_create,
    service_get,
    service_list,
    service_publish,
    service_update,
)
from mcp_eregistrations_bpa.tools.workflows import (
    register_workflow_tools,
    workflow_cancel,
    workflow_chain,
    workflow_confirm,
    workflow_continue,
    workflow_describe,
    workflow_execute,
    workflow_list,
    workflow_retry,
    workflow_rollback,
    workflow_search,
    workflow_start_interactive,
    workflow_status,
)

__all__ = [
    # Service tools
    "service_list",
    "service_get",
    "service_create",
    "service_update",
    "service_publish",
    "service_activate",
    "register_service_tools",
    # Registration tools
    "registration_list",
    "registration_get",
    "registration_create",
    "registration_delete",
    "registration_activate",
    "serviceregistration_link",
    "register_registration_tools",
    # Registration institution tools
    "registrationinstitution_list",
    "registrationinstitution_get",
    "registrationinstitution_create",
    "registrationinstitution_delete",
    "registrationinstitution_list_by_institution",
    "institution_discover",
    "institution_create",
    "register_registration_institution_tools",
    # Field tools
    "field_list",
    "field_get",
    "register_field_tools",
    # Form tools
    "form_get",
    "form_component_get",
    "form_component_add",
    "form_component_update",
    "form_component_remove",
    "form_component_move",
    "form_update",
    "register_form_tools",
    # Form.io component builders
    "build_textfield",
    "build_number",
    "build_select",
    "build_checkbox",
    "build_textarea",
    "build_panel",
    "build_columns",
    # Determinant tools
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
    # Behaviour/Effect tools
    "componentbehaviour_list",
    "componentbehaviour_get",
    "componentbehaviour_get_by_component",
    "effect_create",
    "effect_delete",
    "register_behaviour_tools",
    # Component action tools
    "componentaction_get",
    "componentaction_get_by_component",
    "register_action_tools",
    # Bot tools
    "bot_list",
    "bot_get",
    "bot_create",
    "bot_update",
    "bot_delete",
    "bot_validate",
    "bot_upgrade_version",
    "register_bot_tools",
    # External service tools
    "muleservice_list",
    "muleservice_get",
    "register_external_service_tools",
    # Classification tools
    "classification_list",
    "classification_get",
    "classification_create",
    "classification_update",
    "classification_export_csv",
    "register_classification_tools",
    # Notification tools
    "notification_list",
    "notification_create",
    "register_notification_tools",
    # Role tools
    "role_list",
    "role_get",
    "role_create",
    "role_update",
    "role_delete",
    "roleinstitution_create",
    "roleregistration_create",
    "register_role_tools",
    # Role status tools
    "rolestatus_get",
    "rolestatus_create",
    "rolestatus_update",
    "rolestatus_delete",
    "register_role_status_tools",
    # Role unit tools
    "roleunit_list",
    "roleunit_get",
    "roleunit_create",
    "roleunit_delete",
    "register_role_unit_tools",
    # Message tools
    "message_list",
    "message_get",
    "message_create",
    "message_update",
    "message_delete",
    "register_message_tools",
    # Analysis tools
    "analyze_service",
    "register_analysis_tools",
    # Document requirement tools
    "requirement_list",
    "documentrequirement_list",
    "documentrequirement_create",
    "documentrequirement_update",
    "documentrequirement_delete",
    "register_document_requirement_tools",
    # Cost tools
    "cost_create_fixed",
    "cost_create_formula",
    "cost_update",
    "cost_delete",
    "register_cost_tools",
    # Audit tools
    "audit_list",
    "audit_get",
    "register_audit_tools",
    # Rollback tools
    "rollback",
    "rollback_history",
    "rollback_cleanup",
    "register_rollback_tools",
    # Export tools
    "service_export_raw",
    "service_to_yaml",
    "service_copy",
    "register_export_tools",
    # Workflow orchestration tools
    "workflow_list",
    "workflow_describe",
    "workflow_search",
    "workflow_execute",
    "workflow_status",
    "workflow_cancel",
    "workflow_retry",
    "workflow_rollback",
    "workflow_chain",
    "workflow_start_interactive",
    "workflow_continue",
    "workflow_confirm",
    "register_workflow_tools",
    # Debug tools
    "debug_scan",
    "debug_investigate",
    "debug_fix",
    "debug_fix_batch",
    "debug_group_issues",
    "debug_plan",
    "debug_verify",
    "register_debug_tools",
]

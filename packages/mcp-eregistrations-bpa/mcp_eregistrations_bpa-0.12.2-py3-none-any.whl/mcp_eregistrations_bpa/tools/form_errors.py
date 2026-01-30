"""Form tool error codes for programmatic handling.

This module defines error codes for Form MCP tool operations.
Error codes follow the format: FORM_XXX where XXX is a 3-digit number.

Usage in ToolError messages:
    raise ToolError(f"[{FormErrorCode.DUPLICATE_KEY}] Component key already exists")

The format "[ERROR_CODE] message" allows automation tools to:
1. Parse the error code programmatically
2. Handle specific error types differently
3. Provide localized error messages
"""

from __future__ import annotations


class FormErrorCode:
    """Error codes for Form MCP tool operations.

    Error codes are strings in the format FORM_XXX.
    """

    # Validation errors (001-010)
    INVALID_FORM_TYPE = "FORM_001"
    SERVICE_NOT_FOUND = "FORM_002"
    COMPONENT_NOT_FOUND = "FORM_003"
    DUPLICATE_KEY = "FORM_004"
    INVALID_PARENT = "FORM_005"
    MISSING_REQUIRED_PROPERTY = "FORM_006"
    KEY_CHANGE_NOT_ALLOWED = "FORM_007"
    INVALID_POSITION = "FORM_008"
    CIRCULAR_REFERENCE = "FORM_009"

    # Additional operation errors (010-020)
    NO_UPDATES_PROVIDED = "FORM_010"

"""Authentication module for Keycloak OIDC and CAS.

This module provides authentication for both:
- Keycloak: OIDC/PKCE authentication (modern BPA systems)
- CAS: OAuth2 Basic Auth authentication (legacy BPA systems)

Both flows include browser-based login, token management, automatic refresh,
and permission enforcement.

Permission enforcement usage in MCP tools:
    @mcp.tool()
    async def service_create(name: str) -> dict[str, object]:
        # Ensure write permission before proceeding
        access_token = await ensure_write_permission()
        # ... use access_token for BPA API call
"""

from mcp_eregistrations_bpa.auth.callback import CallbackServer
from mcp_eregistrations_bpa.auth.cas import perform_cas_browser_login
from mcp_eregistrations_bpa.auth.oidc import (
    OIDCConfig,
    build_authorization_url,
    discover_oidc_config,
    generate_pkce_pair,
    generate_state,
    perform_browser_login,
)
from mcp_eregistrations_bpa.auth.permissions import (
    PERMISSION_SERVICE_DESIGNER,
    PERMISSION_VIEWER,
    WRITE_PERMISSIONS,
    check_permission,
    ensure_authenticated,
    ensure_write_permission,
)
from mcp_eregistrations_bpa.auth.token_manager import (
    TokenManager,
    TokenResponse,
    exchange_code_for_tokens,
)

__all__ = [
    # OIDC (Keycloak)
    "OIDCConfig",
    "discover_oidc_config",
    "generate_pkce_pair",
    "generate_state",
    "build_authorization_url",
    "perform_browser_login",
    "CallbackServer",
    # CAS (Legacy)
    "perform_cas_browser_login",
    # Token management
    "TokenManager",
    "TokenResponse",
    "exchange_code_for_tokens",
    # Permissions
    "PERMISSION_VIEWER",
    "PERMISSION_SERVICE_DESIGNER",
    "WRITE_PERMISSIONS",
    "ensure_authenticated",
    "ensure_write_permission",
    "check_permission",
]

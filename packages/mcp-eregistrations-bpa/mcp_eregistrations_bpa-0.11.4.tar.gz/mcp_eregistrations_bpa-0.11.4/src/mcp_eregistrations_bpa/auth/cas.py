"""CAS (eRegistrations custom OAuth2) authentication implementation.

This module handles CAS authentication for legacy BPA systems that don't use Keycloak.
Key differences from Keycloak OIDC:
- No PKCE support (uses client_secret with Basic Auth)
- No OIDC discovery endpoint (endpoints must be configured)
- Authorization endpoint is SPA-based (/cas/spa.html#/)
- User roles fetched from separate PARTC service
"""

import base64
import logging
import secrets
from urllib.parse import urlencode

import httpx

from mcp_eregistrations_bpa.auth.token_manager import TokenResponse
from mcp_eregistrations_bpa.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


def generate_state() -> str:
    """Generate a cryptographically secure state parameter.

    Returns:
        A random state string for CSRF protection.
    """
    return secrets.token_urlsafe(16)


def build_cas_authorization_url(
    cas_authorization_base: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "any",
    lang: str = "en",
) -> str:
    """Build CAS authorization URL (no PKCE).

    CAS uses a SPA-based authorization endpoint with hash fragment parameters.

    Args:
        cas_authorization_base: The CAS authorization base URL
            (e.g., {CAS_URL}/cas/spa.html)
        client_id: The OAuth2 client ID.
        redirect_uri: The local callback URL.
        state: The state parameter for CSRF protection.
        scope: OAuth scope (CAS uses "any").
        lang: Language code for the login page.

    Returns:
        The complete authorization URL to open in browser.
    """
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "lang": lang,
    }
    # CAS uses hash fragment (#/) for SPA routing
    return f"{cas_authorization_base}#/?{urlencode(params)}"


def _build_basic_auth_header(client_id: str, client_secret: str) -> str:
    """Build HTTP Basic Auth header value.

    Args:
        client_id: The OAuth2 client ID.
        client_secret: The OAuth2 client secret.

    Returns:
        The Authorization header value (e.g., "Basic base64(client_id:secret)").
    """
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def exchange_code_for_tokens_cas(
    token_endpoint: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Exchange authorization code for tokens using CAS (Basic Auth).

    Unlike Keycloak PKCE flow, CAS requires:
    - Authorization: Basic base64(client_id:client_secret) header
    - No code_verifier (no PKCE)

    Args:
        token_endpoint: The CAS token endpoint (e.g., {CAS_URL}/access_token).
        code: The authorization code from callback.
        redirect_uri: The redirect URI used in authorization.
        client_id: The OAuth2 client ID.
        client_secret: The OAuth2 client secret.

    Returns:
        TokenResponse with access and refresh tokens.

    Raises:
        AuthenticationError: If token exchange fails.
    """
    auth_header = _build_basic_auth_header(client_id, client_secret)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_endpoint,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get(
                    "error_description", error_data.get("error", "")
                )
            except Exception:
                pass
            raise AuthenticationError(
                f"CAS auth failed: {error_detail or 'Token exchange failed'}. "
                "Verify CAS_CLIENT_ID and CAS_CLIENT_SECRET."
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(
                f"Cannot connect to CAS: {e}. "
                "Verify CAS_URL is correct and the server is accessible."
            ) from e

        try:
            data = response.json()
        except Exception as e:
            raise AuthenticationError(
                f"CAS returned invalid response: {e}. Contact administrator."
            ) from e

        if "access_token" not in data:
            raise AuthenticationError(
                "CAS response missing access_token. "
                "Verify CAS_CLIENT_ID and CAS_CLIENT_SECRET."
            )

        return TokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get(
                "expires_in", 28800
            ),  # Default 8 hours if not specified
            token_type=data.get("token_type", "Bearer"),
        )


async def refresh_tokens_cas(
    token_endpoint: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Refresh access token using CAS (Basic Auth).

    Args:
        token_endpoint: The CAS token endpoint.
        refresh_token: The refresh token.
        client_id: The OAuth2 client ID.
        client_secret: The OAuth2 client secret.

    Returns:
        TokenResponse with new access and refresh tokens.

    Raises:
        AuthenticationError: If refresh fails.
    """
    auth_header = _build_basic_auth_header(client_id, client_secret)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_endpoint,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(
                "CAS session expired. Please run auth_login again."
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(
                f"Cannot refresh CAS session: {e}. Please try again."
            ) from e

        data = response.json()
        return TokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in", 28800),  # Default 8 hours
            token_type=data.get("token_type", "Bearer"),
        )


async def fetch_user_roles_from_partc(
    partc_url: str,
    access_token: str,
) -> list[str]:
    """Fetch user roles from PARTC service.

    CAS doesn't include all roles in the JWT, so we need to fetch them
    from the PARTC user attributes endpoint.

    Args:
        partc_url: The PARTC user attributes URL (e.g., {PARTC_URL}/user/attributes).
        access_token: The access token for authorization.

    Returns:
        List of role strings.

    Raises:
        AuthenticationError: If role fetching fails.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                partc_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "Failed to fetch PARTC roles: HTTP %d", e.response.status_code
            )
            return []  # Return empty roles rather than failing auth
        except httpx.RequestError as e:
            logger.warning("Failed to connect to PARTC: %s", e)
            return []  # Return empty roles rather than failing auth

        data = response.json()

        # PARTC returns array of role strings
        if isinstance(data, list):
            return [str(role) for role in data if role]

        # Handle potential wrapper object
        if isinstance(data, dict):
            roles = data.get("roles") or data.get("attributes") or []
            if isinstance(roles, list):
                return [str(role) for role in roles if role]

        return []


async def perform_cas_browser_login() -> dict[str, object]:
    """Perform browser-based CAS login flow.

    This is the CAS equivalent of perform_browser_login() in oidc.py.

    Returns:
        dict: Authentication result with user email and session duration.

    Raises:
        AuthenticationError: If authentication fails.
    """
    import webbrowser

    from mcp_eregistrations_bpa.auth.callback import CallbackServer
    from mcp_eregistrations_bpa.config import load_config

    logger.info("Starting CAS browser login flow...")

    # Load configuration
    config = load_config()

    if not config.cas_url or not config.cas_client_id or not config.cas_client_secret:
        raise AuthenticationError(
            "CAS configuration incomplete. "
            "Set CAS_URL, CAS_CLIENT_ID, and CAS_CLIENT_SECRET."
        )

    logger.debug("CAS URL: %s", config.cas_url)

    # Generate state (no PKCE for CAS)
    state = generate_state()
    logger.debug("Generated state parameter")

    # Start callback server on fixed port (CAS requires exact redirect_uri match)
    callback_server = CallbackServer(port=config.cas_callback_port)
    callback_server.start()
    logger.info("Callback server started on port %d", callback_server.port)

    try:
        # Build CAS authorization URL (no PKCE)
        auth_url = build_cas_authorization_url(
            cas_authorization_base=config.cas_authorization_url or "",
            client_id=config.cas_client_id,
            redirect_uri=callback_server.redirect_uri,
            state=state,
        )
        logger.debug("CAS auth URL built: %s...", auth_url[:80])

        # Open browser
        logger.info("Opening browser for CAS authentication...")
        if not webbrowser.open(auth_url):
            logger.error("Failed to open browser")
            return {
                "error": True,
                "message": (
                    "Cannot open browser for authentication. "
                    f"Please open this URL manually: {auth_url}"
                ),
            }

        # Wait for callback
        logger.info("Waiting for CAS OAuth callback...")
        code = await callback_server.wait_for_callback(expected_state=state)
        logger.info("Received authorization code from CAS")

        # Exchange code for tokens (using Basic Auth, not PKCE)
        logger.info("Exchanging code for tokens via CAS...")
        token_response = await exchange_code_for_tokens_cas(
            token_endpoint=config.cas_token_url or "",
            code=code,
            redirect_uri=callback_server.redirect_uri,
            client_id=config.cas_client_id,
            client_secret=config.cas_client_secret.get_secret_value(),
        )
        logger.info("CAS token exchange successful")

        # Get token manager and store tokens
        from mcp_eregistrations_bpa.server import get_token_manager

        token_manager = get_token_manager()
        token_manager.store_tokens(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            expires_in=token_response.expires_in,
            token_endpoint=config.cas_token_url,
            client_id=config.cas_client_id,
        )

        # Store client_secret for CAS token refresh (needed because CAS uses Basic Auth)
        token_manager._cas_client_secret = config.cas_client_secret.get_secret_value()

        # Fetch additional roles from PARTC if configured
        if config.partc_user_attributes_url:
            logger.info("Fetching user roles from PARTC...")
            partc_roles = await fetch_user_roles_from_partc(
                partc_url=config.partc_user_attributes_url,
                access_token=token_response.access_token,
            )
            if partc_roles:
                # Merge PARTC roles with JWT roles
                existing_roles = set(token_manager.permissions)
                for role in partc_roles:
                    if role not in existing_roles:
                        token_manager._permissions.append(role)
                logger.info("Added %d roles from PARTC", len(partc_roles))

        logger.info("Tokens stored for user: %s", token_manager.user_email)

        result = {
            "success": True,
            "message": (
                f"Authenticated as {token_manager.user_email} via CAS. "
                f"Session valid for {token_manager.expires_in_minutes} minutes."
            ),
            "user_email": token_manager.user_email,
            "session_expires_in_minutes": token_manager.expires_in_minutes,
            "auth_provider": "cas",
        }
        logger.info("CAS browser login complete")
        return result

    except AuthenticationError:
        logger.exception("CAS authentication error")
        raise
    except Exception as e:
        logger.exception("Unexpected error during CAS authentication")
        raise AuthenticationError(
            f"CAS authentication failed: {e}. Please try again."
        ) from e
    finally:
        logger.debug("Stopping callback server")
        callback_server.stop()

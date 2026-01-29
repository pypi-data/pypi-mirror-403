"""Configuration management for MCP server.

Loads configuration from environment variables only.

Supports two authentication providers:
- Keycloak: Standard OIDC with PKCE (default)
- CAS: Legacy eRegistrations OAuth2 server (no PKCE, Basic Auth)

Instance Isolation:
Each BPA instance gets its own data directory based on hostname.
This ensures tokens, audit logs, and rollback states are isolated.
"""

import hashlib
import os
import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

from mcp_eregistrations_bpa.exceptions import ConfigurationError


class AuthProvider(str, Enum):
    """Authentication provider type."""

    KEYCLOAK = "keycloak"  # Standard OIDC with PKCE
    CAS = "cas"  # Legacy eRegistrations OAuth2 (no PKCE, Basic Auth)


# XDG-compliant data directory
CONFIG_DIR = Path.home() / ".config" / "mcp-eregistrations-bpa"


def _generate_instance_slug(url: str) -> str:
    """Generate a filesystem-safe slug from a BPA instance URL.

    Creates a human-readable identifier from the hostname, plus a short hash
    for uniqueness. Format: {sanitized_hostname}-{short_hash}

    Examples:
        https://bpa.dev.els.eregistrations.org -> els-dev-a1b2c3
        https://bpa.test.cuba.eregistrations.org -> cuba-test-d4e5f6

    Args:
        url: The BPA instance URL.

    Returns:
        A filesystem-safe slug like "els-dev-a1b2c3".
    """
    parsed = urlparse(url)
    hostname = parsed.netloc or parsed.path  # Handle edge cases

    # Extract meaningful parts from hostname
    # e.g., "bpa.dev.els.eregistrations.org" ->
    # ["bpa", "dev", "els", "eregistrations", "org"]
    parts = hostname.lower().split(".")

    # Remove common prefixes/suffixes for cleaner slug
    skip_parts = {"bpa", "eregistrations", "org", "com", "www"}
    meaningful_parts = [p for p in parts if p not in skip_parts and p]

    # Build readable slug (reversed to get country/env first: "els-dev")
    if meaningful_parts:
        slug_base = "-".join(reversed(meaningful_parts[:2]))  # Max 2 parts
    else:
        slug_base = "default"

    # Add short hash for uniqueness (handles edge cases)
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:6]
    slug = f"{slug_base}-{url_hash}"

    # Sanitize: only allow alphanumeric and hyphens
    slug = re.sub(r"[^a-z0-9-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")

    return slug


def get_instance_data_dir(bpa_url: str | None = None) -> Path:
    """Get the instance-specific data directory.

    Each BPA instance gets its own subdirectory under CONFIG_DIR.
    This isolates databases, tokens, and logs per instance.

    Args:
        bpa_url: BPA instance URL. If None, reads from environment.

    Returns:
        Path to instance-specific data directory.
        Falls back to CONFIG_DIR if no URL configured.
        Creates the directory if it doesn't exist.
    """
    if bpa_url is None:
        bpa_url = os.environ.get("BPA_INSTANCE_URL")

    if not bpa_url:
        # Fallback to base config dir (backward compatible)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return CONFIG_DIR

    slug = _generate_instance_slug(bpa_url)
    instance_dir = CONFIG_DIR / "instances" / slug
    instance_dir.mkdir(parents=True, exist_ok=True)
    return instance_dir


@lru_cache(maxsize=1)
def get_current_instance_id() -> str | None:
    """Get the instance ID for the current BPA instance (cached).

    Returns:
        Instance slug or None if not configured.
    """
    bpa_url = os.environ.get("BPA_INSTANCE_URL")
    if not bpa_url:
        return None
    return _generate_instance_slug(bpa_url)


class Config(BaseModel):
    """MCP server configuration."""

    bpa_instance_url: str

    # Keycloak configuration (standard OIDC with PKCE)
    keycloak_client_id: str = "mcp-eregistrations-bpa"
    keycloak_url: str | None = None
    keycloak_realm: str | None = None

    # CAS configuration (legacy eRegistrations OAuth2)
    cas_url: str | None = None
    cas_client_id: str | None = None
    cas_client_secret: SecretStr | None = Field(
        default=None, repr=False
    )  # Required for CAS (no PKCE)
    cas_callback_port: int = 8914  # Fixed port for CAS redirect_uri

    @field_validator("bpa_instance_url", "keycloak_url", "cas_url")
    @classmethod
    def validate_https(cls, v: str | None) -> str | None:
        """Validate that URLs use HTTPS and have valid structure."""
        if v is None:
            return None
        if not v:
            raise ValueError("URL cannot be empty")
        if v.startswith("http://"):
            raise ValueError(
                "URL must use HTTPS: "
                "Security requires encrypted connections. "
                "Update URL to use https:// scheme."
            )
        if not v.startswith("https://"):
            raise ValueError("URL must start with https://")
        # Validate URL structure
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("URL must have a valid host")
        if parsed.query or parsed.fragment:
            raise ValueError("URL must not contain query string or fragment")
        return v.rstrip("/")  # Normalize: remove trailing slash

    @model_validator(mode="after")
    def validate_cas_config(self) -> "Config":
        """Validate CAS configuration if CAS URL is provided."""
        if self.cas_url:
            if not self.cas_client_id:
                raise ValueError(
                    "CAS_CLIENT_ID required when CAS_URL is set. "
                    "CAS authentication requires a client ID."
                )
            # Check SecretStr: must exist and have non-empty value
            if (
                not self.cas_client_secret
                or not self.cas_client_secret.get_secret_value()
            ):
                raise ValueError(
                    "CAS_CLIENT_SECRET required when CAS_URL is set. "
                    "CAS uses Basic Auth instead of PKCE."
                )
        return self

    @property
    def auth_provider(self) -> AuthProvider:
        """Detect authentication provider based on configuration.

        Returns CAS if cas_url is configured, otherwise Keycloak.
        """
        if self.cas_url:
            return AuthProvider.CAS
        return AuthProvider.KEYCLOAK

    @property
    def oidc_discovery_url(self) -> str:
        """Get the OIDC discovery URL (Keycloak only).

        If keycloak_url and keycloak_realm are provided, constructs
        the standard Keycloak realm discovery URL. Otherwise, falls
        back to BPA instance URL for discovery.

        Note: CAS does not support OIDC discovery.

        Returns:
            The URL for .well-known/openid-configuration discovery.
        """
        if self.keycloak_url and self.keycloak_realm:
            # Standard Keycloak realm URL pattern
            return f"{self.keycloak_url}/realms/{self.keycloak_realm}"
        elif self.keycloak_url:
            # Keycloak URL provided but no realm - use as base
            return self.keycloak_url
        else:
            # Default: assume OIDC discovery at BPA URL
            return self.bpa_instance_url

    @property
    def cas_authorization_url(self) -> str | None:
        """Get the CAS authorization URL (CAS only).

        Returns:
            The CAS SPA authorization URL, or None if not using CAS.
        """
        if not self.cas_url:
            return None
        return f"{self.cas_url}/cas/spa.html"

    @property
    def cas_token_url(self) -> str | None:
        """Get the CAS token endpoint URL (CAS only).

        Returns:
            The CAS token URL, or None if not using CAS.
        """
        if not self.cas_url:
            return None
        return f"{self.cas_url}/access_token"

    @property
    def cas_public_key_url(self) -> str | None:
        """Get the CAS public key URL for JWT validation (CAS only).

        Returns:
            The CAS public key URL, or None if not using CAS.
        """
        if not self.cas_url:
            return None
        return f"{self.cas_url}/user/publicKey"

    @property
    def partc_url(self) -> str | None:
        """Derive PARTC URL from CAS URL.

        PARTC shares the same base as CAS, just different path:
        - CAS:   https://eid.test.cuba.eregistrations.org/cback/v1.0
        - PARTC: https://eid.test.cuba.eregistrations.org/partc/v1.0

        Returns:
            The PARTC base URL, or None if CAS not configured or URL
            doesn't contain /cback/ path.
        """
        if not self.cas_url:
            return None
        if "/cback/" not in self.cas_url:
            # Non-standard CAS URL - cannot derive PARTC URL
            return None
        return self.cas_url.replace("/cback/", "/partc/")

    @property
    def partc_user_attributes_url(self) -> str | None:
        """Get the PARTC user attributes URL (CAS only).

        Returns:
            The PARTC URL for fetching user roles, or None if not configured.
        """
        if not self.partc_url:
            return None
        return f"{self.partc_url}/user/attributes"

    @property
    def instance_id(self) -> str:
        """Get the unique instance ID for this BPA instance.

        Used for data isolation (database, logs, etc.).

        Returns:
            A filesystem-safe slug like "els-dev-a1b2c3".
        """
        return _generate_instance_slug(self.bpa_instance_url)

    @property
    def instance_data_dir(self) -> Path:
        """Get the instance-specific data directory.

        Returns:
            Path to the directory for this instance's data.
        """
        return get_instance_data_dir(self.bpa_instance_url)


def load_config() -> Config:
    """Load configuration from environment variables.

    Required environment variables:
        BPA_INSTANCE_URL: The BPA instance URL (required)

    Optional environment variables:
        KEYCLOAK_URL: Keycloak server URL
        KEYCLOAK_REALM: Keycloak realm name
        KEYCLOAK_CLIENT_ID: Keycloak client ID (default: mcp-eregistrations-bpa)
        CAS_URL: CAS server URL (for legacy auth, PARTC URL derived automatically)
        CAS_CLIENT_ID: CAS client ID
        CAS_CLIENT_SECRET: CAS client secret

    Returns:
        Validated Config object.

    Raises:
        ConfigurationError: If required configuration is missing or invalid.
    """
    url = os.environ.get("BPA_INSTANCE_URL")

    if not url:
        raise ConfigurationError(
            "BPA_INSTANCE_URL environment variable is required. "
            "Set it in your MCP server configuration."
        )

    # Build config from environment variables
    # Use Any because Pydantic handles type coercion (str -> SecretStr, etc.)
    config_kwargs: dict[str, Any] = {"bpa_instance_url": url}

    # Keycloak configuration
    if keycloak_client_id := os.environ.get("KEYCLOAK_CLIENT_ID"):
        config_kwargs["keycloak_client_id"] = keycloak_client_id

    if keycloak_url := os.environ.get("KEYCLOAK_URL"):
        config_kwargs["keycloak_url"] = keycloak_url

    if keycloak_realm := os.environ.get("KEYCLOAK_REALM"):
        config_kwargs["keycloak_realm"] = keycloak_realm

    # CAS configuration
    if cas_url := os.environ.get("CAS_URL"):
        config_kwargs["cas_url"] = cas_url

    if cas_client_id := os.environ.get("CAS_CLIENT_ID"):
        config_kwargs["cas_client_id"] = cas_client_id

    if cas_client_secret := os.environ.get("CAS_CLIENT_SECRET"):
        config_kwargs["cas_client_secret"] = cas_client_secret

    if cas_callback_port := os.environ.get("CAS_CALLBACK_PORT"):
        config_kwargs["cas_callback_port"] = int(cas_callback_port)

    # Validate and return config
    try:
        return Config(**config_kwargs)
    except ValueError as e:
        raise ConfigurationError(str(e)) from e

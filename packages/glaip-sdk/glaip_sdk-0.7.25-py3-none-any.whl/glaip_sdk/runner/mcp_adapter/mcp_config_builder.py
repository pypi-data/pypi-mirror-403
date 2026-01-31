"""MCP configuration builder helper.

This module provides utilities for building MCP configurations,
particularly for handling authentication conversion to headers.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from typing import Any

from gllm_core.utils import LoggerManager

logger = LoggerManager().get_logger(__name__)


class MCPConfigBuilder:
    """Helper class for building MCP configurations.

    Handles authentication-to-headers conversion and configuration validation.
    Simplified version focused on local MCP support needs.
    """

    @staticmethod
    def build_headers_from_auth(authentication: dict[str, Any]) -> dict[str, str] | None:
        """Build HTTP headers from authentication configuration.

        Args:
            authentication: Authentication configuration dict with 'type' and auth-specific fields.

        Returns:
            dict[str, str] | None: HTTP headers or None if invalid/no-auth.
        """
        if not authentication or "type" not in authentication:
            return None

        auth_type = str(authentication["type"]).lower()

        # Dispatch to type-specific handlers
        handlers = {
            "no-auth": MCPConfigBuilder._handle_no_auth,
            "custom-header": MCPConfigBuilder._handle_custom_header,
            "bearer-token": MCPConfigBuilder._handle_bearer_token,
            "api-key": MCPConfigBuilder._handle_api_key,
        }

        handler = handlers.get(auth_type)
        if handler:
            return handler(authentication)

        logger.warning("Unsupported authentication type: %s", auth_type)
        return None

    @staticmethod
    def _handle_no_auth(authentication: dict[str, Any]) -> None:  # noqa: ARG004
        """Handle no-auth type."""
        return None

    @staticmethod
    def _handle_custom_header(authentication: dict[str, Any]) -> dict[str, str] | None:
        """Handle custom-header auth type."""
        headers = authentication.get("headers")
        if isinstance(headers, dict):
            cleaned_headers = MCPConfigBuilder._clean_headers(headers)
            if cleaned_headers:
                return cleaned_headers

        logger.warning("custom-header auth requires 'headers' dict with at least one non-null key/value")
        return None

    @staticmethod
    def _clean_headers(headers: dict[str, Any]) -> dict[str, str] | None:
        """Clean header dict by filtering None keys/values and stringifying values.

        Args:
            headers: Raw headers dict potentially containing None or non-string values.

        Returns:
            Cleaned headers dict with string keys/values, or None if empty after cleaning.
        """
        cleaned: dict[str, str] = {}
        for key, value in headers.items():
            if key is None:
                logger.warning("Dropping header with null key")
                continue
            if value is None:
                logger.warning("Dropping header '%s' with null value", key)
                continue
            cleaned[str(key)] = str(value)

        return cleaned if cleaned else None

    @staticmethod
    def _handle_bearer_token(authentication: dict[str, Any]) -> dict[str, str] | None:
        """Handle bearer-token auth type."""
        headers = authentication.get("headers")
        if isinstance(headers, dict):
            return MCPConfigBuilder._clean_headers(headers)
        token = authentication.get("token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        logger.warning("bearer-token auth requires 'token' field or 'headers' dict")
        return None

    @staticmethod
    def _handle_api_key(authentication: dict[str, Any]) -> dict[str, str] | None:
        """Handle api-key auth type."""
        headers = authentication.get("headers")
        if isinstance(headers, dict):
            return MCPConfigBuilder._clean_headers(headers)
        key = authentication.get("key")
        value = authentication.get("value")
        if key and value:
            return {str(key): str(value)}
        logger.warning("api-key auth requires 'key' and 'value' fields or 'headers' dict")
        return None

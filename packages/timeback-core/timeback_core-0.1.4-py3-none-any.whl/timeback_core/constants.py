"""
Timeback API Endpoints

URL constants for Timeback services by environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Environment

# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

ENV_VAR_ENV = "TIMEBACK_ENV"
ENV_VAR_BASE_URL = "TIMEBACK_BASE_URL"
ENV_VAR_AUTH_URL = "TIMEBACK_TOKEN_URL"
ENV_VAR_CLIENT_ID = "TIMEBACK_CLIENT_ID"
ENV_VAR_CLIENT_SECRET = "TIMEBACK_CLIENT_SECRET"

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE URLS BY ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════════════════

# BeyondAI platform endpoints
SERVICE_URLS: dict[str, dict[str, str]] = {
    "staging": {
        "api": "https://api.staging.alpha-1edtech.ai",
        "caliper": "https://caliper.staging.alpha-1edtech.ai",
        "token": "https://staging-beyond-timeback-api-2-idp.auth.us-east-1.amazoncognito.com/oauth2/token",
    },
    "production": {
        "api": "https://api.alpha-1edtech.ai",
        "caliper": "https://caliper.alpha-1edtech.ai",
        "token": "https://prod-beyond-timeback-api-2-idp.auth.us-east-1.amazoncognito.com/oauth2/token",
    },
}


def get_service_urls(env: Environment) -> dict[str, str]:
    """
    Get service URLs for a given environment.

    Args:
        env: Deployment environment (staging or production)

    Returns:
        Dict with keys: oneroster, caliper, edubridge, auth_url
    """
    urls = SERVICE_URLS[env]
    return {
        "oneroster": urls["api"],
        "caliper": urls["caliper"],
        "edubridge": urls["api"],
        "auth_url": urls["token"],
    }


__all__ = [
    "ENV_VAR_AUTH_URL",
    "ENV_VAR_BASE_URL",
    "ENV_VAR_CLIENT_ID",
    "ENV_VAR_CLIENT_SECRET",
    "ENV_VAR_ENV",
    "SERVICE_URLS",
    "get_service_urls",
]

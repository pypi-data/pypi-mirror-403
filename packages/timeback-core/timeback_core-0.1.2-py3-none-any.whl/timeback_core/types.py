"""
Timeback Core Types

Configuration types for the unified Timeback client.
"""

from __future__ import annotations

from typing import Literal, TypedDict

# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM & ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════════════════

Platform = Literal["BEYOND_AI", "LEARNWITH_AI"]
"""Timeback platform identifier."""

Environment = Literal["staging", "production"]
"""Timeback deployment environment."""


class AuthCredentials(TypedDict, total=False):
    """OAuth2 client credentials."""

    client_id: str
    """OAuth2 client ID."""

    client_secret: str
    """OAuth2 client secret."""

    auth_url: str
    """OAuth2 token endpoint URL (required for explicit config)."""


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE URLS
# ═══════════════════════════════════════════════════════════════════════════════


class ServiceUrls(TypedDict, total=False):
    """Explicit URLs for each service."""

    oneroster: str
    """OneRoster API base URL."""

    caliper: str
    """Caliper API base URL."""

    edubridge: str
    """Edubridge API base URL."""


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT CONFIG
# ═══════════════════════════════════════════════════════════════════════════════


class EnvConfig(TypedDict, total=False):
    """Environment-based configuration."""

    env: Environment
    """Deployment environment (staging or production)."""

    client_id: str
    """OAuth2 client ID."""

    client_secret: str
    """OAuth2 client secret."""

    timeout: float
    """Request timeout in seconds."""


class BaseUrlConfig(TypedDict, total=False):
    """Single base URL configuration."""

    base_url: str
    """Base URL for all services."""

    auth_url: str
    """OAuth2 token endpoint URL."""

    client_id: str
    """OAuth2 client ID."""

    client_secret: str
    """OAuth2 client secret."""

    timeout: float
    """Request timeout in seconds."""


class ServicesConfig(TypedDict, total=False):
    """Explicit services configuration."""

    services: ServiceUrls
    """Service-specific URLs."""

    auth_url: str
    """OAuth2 token endpoint URL."""

    client_id: str
    """OAuth2 client ID."""

    client_secret: str
    """OAuth2 client secret."""

    timeout: float
    """Request timeout in seconds."""


# Union type for all config modes
TimebackClientConfig = EnvConfig | BaseUrlConfig | ServicesConfig
"""
Configuration for the unified Timeback client.

Supports three modes:
- **Environment**: `{"env": "staging", "client_id": "...", "client_secret": "..."}`
- **Base URL**: `{"base_url": "...", "auth_url": "...", "client_id": "...", "client_secret": "..."}`
- **Services**: `{"services": {...}, "auth_url": "...", "client_id": "...", "client_secret": "..."}`
"""


# ═══════════════════════════════════════════════════════════════════════════════
# BROADCAST TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class BroadcastSuccess[T](TypedDict):
    """Successful broadcast result."""

    ok: Literal[True]
    value: T


class BroadcastFailure(TypedDict):
    """Failed broadcast result."""

    ok: Literal[False]
    error: Exception


BroadcastResult = BroadcastSuccess | BroadcastFailure
"""Result of a broadcast operation for a single client."""


__all__ = [
    "AuthCredentials",
    "BaseUrlConfig",
    "BroadcastFailure",
    "BroadcastResult",
    "BroadcastSuccess",
    "EnvConfig",
    "Environment",
    "Platform",
    "ServiceUrls",
    "ServicesConfig",
    "TimebackClientConfig",
]

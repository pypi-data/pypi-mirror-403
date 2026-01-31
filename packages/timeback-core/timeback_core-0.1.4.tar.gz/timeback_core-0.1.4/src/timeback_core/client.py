"""
Timeback Client

Unified client for all Timeback education APIs.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from timeback_caliper import CaliperClient
from timeback_edubridge import EdubridgeClient
from timeback_oneroster import OneRosterClient

from .constants import (
    ENV_VAR_AUTH_URL,
    ENV_VAR_CLIENT_ID,
    ENV_VAR_CLIENT_SECRET,
    ENV_VAR_ENV,
)
from .provider import AuthCheckResult, TimebackProvider

if TYPE_CHECKING:
    from .types import Environment, Platform, TimebackClientConfig


class TimebackClient:
    """
    Unified client for Timeback education APIs.

    Provides access to all Timeback APIs with shared authentication:
    - **OneRoster**: Rostering and gradebook data
    - **Edubridge**: Simplified enrollments and analytics
    - **Caliper**: Learning analytics events

    All sub-clients share a single OAuth token cache, reducing auth requests.

    Sub-clients are lazily initialized on first access.

    Example:
        ```python
        from timeback_core import TimebackClient

        # Environment mode
        client = TimebackClient(
            env="staging",
            client_id="your-client-id",
            client_secret="your-client-secret",
        )

        # Access sub-clients
        users = await client.oneroster.users.list()
        analytics = await client.edubridge.analytics.summary()
        await client.caliper.events.send(sensor_id, events)

        # Verify auth is working
        result = await client.check_auth()
        if result["ok"]:
            print(f"Auth verified in {result['latency_ms']}ms")

        # Close when done
        await client.close()
        ```

    Example with context manager:
        ```python
        async with TimebackClient(env="staging", ...) as client:
            users = await client.oneroster.users.list()
        # Client is automatically closed
        ```

    Example with provider:
        ```python
        provider = TimebackProvider(
            platform="BEYOND_AI",
            env="staging",
            client_id="...",
            client_secret="...",
        )

        client = TimebackClient(provider=provider)
        ```
    """

    def __init__(
        self,
        *,
        # Provider mode
        provider: TimebackProvider | None = None,
        # Config modes
        platform: Platform | None = None,
        env: Environment | None = None,
        base_url: str | None = None,
        services: dict[str, str] | None = None,
        auth_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: float = 30.0,
        config: TimebackClientConfig | None = None,
    ) -> None:
        """
        Create a new Timeback client.

        You can configure the client in several ways:

        1. **Provider mode** (pre-built provider):
           ```python
           provider = TimebackProvider(platform="BEYOND_AI", env="staging", ...)
           client = TimebackClient(provider=provider)
           ```

        2. **Environment mode** (recommended):
           ```python
           client = TimebackClient(
               env="staging",  # or "production"
               client_id="...",
               client_secret="...",
           )
           ```

        3. **Base URL mode** (self-hosted):
           ```python
           client = TimebackClient(
               base_url="https://timeback.myschool.edu",
               auth_url="https://timeback.myschool.edu/oauth/token",
               client_id="...",
               client_secret="...",
           )
           ```

        3b. **Base URL mode, no-auth** (local development):
           ```python
           client = TimebackClient(
               base_url="http://localhost:3000",
           )
           ```

        4. **Services mode** (full control):
           ```python
           client = TimebackClient(
               services={
                   "oneroster": "https://roster.example.com",
                   "caliper": "https://analytics.example.com",
                   "edubridge": "https://api.example.com",
               },
               auth_url="https://auth.example.com/token",
               client_id="...",
               client_secret="...",
           )
           ```

        5. **Environment variables** (when no args provided):
           - TIMEBACK_ENV
           - TIMEBACK_CLIENT_ID
           - TIMEBACK_CLIENT_SECRET
           - TIMEBACK_TOKEN_URL (optional)

        Args:
            provider: Pre-built TimebackProvider (overrides other args)
            platform: Platform identifier (BEYOND_AI or LEARNWITH_AI)
            env: Deployment environment ("staging" or "production")
            base_url: Base URL for all services (self-hosted mode)
            services: Service-specific URLs
            auth_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            timeout: Request timeout in seconds
            config: Full configuration dict (alternative to individual args)
        """
        # If provider is passed, use it directly
        if provider is not None:
            self._provider = provider
        else:
            # Build a provider from the config
            self._provider = self._build_provider(
                platform=platform,
                env=env,
                base_url=base_url,
                services=services,
                auth_url=auth_url,
                client_id=client_id,
                client_secret=client_secret,
                timeout=timeout,
                config=config,
            )

        # Lazy-initialized sub-clients
        self._oneroster: OneRosterClient | None = None
        self._edubridge: EdubridgeClient | None = None
        self._caliper: CaliperClient | None = None
        self._closed = False

    def _build_provider(
        self,
        *,
        platform: Platform | None,
        env: Environment | None,
        base_url: str | None,
        services: dict[str, str] | None,
        auth_url: str | None,
        client_id: str | None,
        client_secret: str | None,
        timeout: float,
        config: TimebackClientConfig | None,
    ) -> TimebackProvider:
        """Build a TimebackProvider from the config."""
        # If config dict provided, extract values
        if config is not None:
            env = config.get("env", env)  # type: ignore[union-attr]
            base_url = config.get("base_url", base_url)  # type: ignore[union-attr]
            services = config.get("services", services)  # type: ignore[union-attr]
            auth_url = config.get("auth_url", auth_url)  # type: ignore[union-attr]
            client_id = config.get("client_id", client_id)  # type: ignore[union-attr]
            client_secret = config.get("client_secret", client_secret)  # type: ignore[union-attr]
            timeout = config.get("timeout", timeout)  # type: ignore[union-attr]

        # Fall back to environment variables
        env = env or os.environ.get(ENV_VAR_ENV)  # type: ignore[assignment]
        client_id = client_id or os.environ.get(ENV_VAR_CLIENT_ID)
        client_secret = client_secret or os.environ.get(ENV_VAR_CLIENT_SECRET)
        auth_url = auth_url or os.environ.get(ENV_VAR_AUTH_URL)

        # Build provider based on config mode
        if services:
            # Services mode - auth is required only if auth_url is provided
            if auth_url and (not client_id or not client_secret):
                raise ValueError(
                    "Timeback API credentials are required when auth_url is provided.\n"
                    "  - Pass client_id and client_secret to TimebackClient(), or\n"
                    "  - Set TIMEBACK_CLIENT_ID and TIMEBACK_CLIENT_SECRET environment variables\n"
                )
            return TimebackProvider(
                services=services,
                auth_url=auth_url,
                client_id=client_id,
                client_secret=client_secret,
                timeout=timeout,
            )
        elif base_url:
            # Base URL mode - auth is optional (supports no-auth local mode)
            if auth_url and (not client_id or not client_secret):
                raise ValueError(
                    "Timeback API credentials are required when auth_url is provided.\n"
                    "  - Pass client_id and client_secret to TimebackClient(), or\n"
                    "  - Set TIMEBACK_CLIENT_ID and TIMEBACK_CLIENT_SECRET environment variables\n"
                )
            return TimebackProvider(
                base_url=base_url,
                auth_url=auth_url,
                client_id=client_id,
                client_secret=client_secret,
                timeout=timeout,
            )
        elif env:
            # Environment mode - always requires credentials
            if env not in ("staging", "production"):
                raise ValueError(f"Invalid environment: {env}. Must be 'staging' or 'production'")
            if not client_id:
                raise ValueError(
                    "Timeback API client_id is required.\n"
                    "  - Pass client_id to TimebackClient(), or\n"
                    "  - Set the TIMEBACK_CLIENT_ID environment variable\n"
                )
            if not client_secret:
                raise ValueError(
                    "Timeback API client_secret is required.\n"
                    "  - Pass client_secret to TimebackClient(), or\n"
                    "  - Set the TIMEBACK_CLIENT_SECRET environment variable\n"
                )
            return TimebackProvider(
                platform=platform,
                env=env,  # type: ignore[arg-type]
                client_id=client_id,
                client_secret=client_secret,
                timeout=timeout,
            )
        else:
            raise ValueError(
                "Configuration required. Provide env, base_url, services, provider, "
                "or set TIMEBACK_ENV environment variable."
            )

    # ═══════════════════════════════════════════════════════════════════════════════
    # PROVIDER
    # ═══════════════════════════════════════════════════════════════════════════════

    def get_provider(self) -> TimebackProvider:
        """
        Get the underlying provider for advanced use cases.

        Returns:
            The TimebackProvider instance used by this client
        """
        return self._provider

    # ═══════════════════════════════════════════════════════════════════════════════
    # SUB-CLIENTS (lazy initialization with shared token manager)
    # ═══════════════════════════════════════════════════════════════════════════════

    @property
    def oneroster(self) -> OneRosterClient:
        """
        OneRoster API client for rostering and gradebook operations.

        Lazily initialized on first access. Shares OAuth tokens with
        other sub-clients through the provider.

        Returns:
            The OneRoster client instance

        Raises:
            RuntimeError: If client has been closed or service not configured
        """
        self._assert_open()
        self._assert_service("oneroster")

        if self._oneroster is None:
            self._oneroster = OneRosterClient(provider=self._provider)

        return self._oneroster

    @property
    def edubridge(self) -> EdubridgeClient:
        """
        Edubridge API client for simplified enrollments and analytics.

        Lazily initialized on first access. Shares OAuth tokens with
        other sub-clients through the provider.

        Returns:
            The Edubridge client instance

        Raises:
            RuntimeError: If client has been closed or service not configured
        """
        self._assert_open()
        self._assert_service("edubridge")

        if self._edubridge is None:
            self._edubridge = EdubridgeClient(provider=self._provider)

        return self._edubridge

    @property
    def caliper(self) -> CaliperClient:
        """
        Caliper API client for learning analytics events.

        Lazily initialized on first access. Shares OAuth tokens with
        other sub-clients through the provider.

        Returns:
            The Caliper client instance

        Raises:
            RuntimeError: If client has been closed or service not configured
        """
        self._assert_open()
        self._assert_service("caliper")

        if self._caliper is None:
            self._caliper = CaliperClient(provider=self._provider)

        return self._caliper

    # ═══════════════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════════════

    @property
    def closed(self) -> bool:
        """Check if the client has been closed."""
        return self._closed

    async def check_auth(self) -> AuthCheckResult:
        """
        Verify that OAuth authentication is working.

        Attempts to acquire a token using the provider's credentials.
        Returns a health check result with success/failure and latency info.

        Returns:
            Auth check result with ok, latency_ms, and optional error

        Raises:
            RuntimeError: If client has been closed
        """
        self._assert_open()
        return await self._provider.check_auth()

    async def close(self) -> None:
        """
        Close the client and release resources.

        After calling close():
        - Cached OAuth tokens are invalidated
        - Sub-client references are cleared
        - Further API calls will raise RuntimeError
        """
        if self._closed:
            return

        # Invalidate all cached tokens
        self._provider.invalidate_tokens()

        # Close all initialized sub-clients
        if self._oneroster is not None:
            await self._oneroster.close()
            self._oneroster = None

        if self._edubridge is not None:
            await self._edubridge.close()
            self._edubridge = None

        if self._caliper is not None:
            await self._caliper.close()
            self._caliper = None

        self._closed = True

    async def __aenter__(self) -> TimebackClient:
        """Context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Context manager exit."""
        await self.close()

    # ═══════════════════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════════════════════

    def _assert_open(self) -> None:
        """Raise if the client has been closed."""
        if self._closed:
            raise RuntimeError("TimebackClient has been closed")

    def _assert_service(self, service: str) -> None:
        """Raise if a service is not configured."""
        if not self._provider.has_service(service):  # type: ignore[arg-type]
            raise RuntimeError(f'Service "{service}" is not configured')


__all__ = ["TimebackClient"]

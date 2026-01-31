"""
Timeback Core

Unified client for all Timeback education APIs.

Example:
    ```python
    from timeback_core import TimebackClient

    client = TimebackClient(
        env="staging",
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

    # OneRoster - rostering and gradebook
    users = await client.oneroster.users.list()

    # Edubridge - simplified enrollments and analytics
    analytics = await client.edubridge.analytics.summary()

    # Caliper - learning analytics events
    await client.caliper.events.send(sensor_id, events)

    await client.close()
    ```

For managing multiple clients:
    ```python
    from timeback_core import TimebackManager

    manager = TimebackManager()
    manager.register("alpha", env="production", client_id="...", client_secret="...")
    manager.register("beta", env="production", client_id="...", client_secret="...")

    # Target a specific platform
    users = await manager.get("alpha").oneroster.users.list()

    # Broadcast to all
    results = await manager.broadcast(lambda c: c.oneroster.users.list())

    await manager.close()
    ```
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("timeback-core")
except PackageNotFoundError:
    __version__ = "0.0.0"

import timeback_caliper as Caliper
import timeback_edubridge as Edubridge
import timeback_oneroster as OneRoster
from timeback_common import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    FormattedError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
    format_api_error,
    is_api_error,
)

from .broadcast import BroadcastResults
from .client import TimebackClient
from .constants import (
    ENV_VAR_AUTH_URL,
    ENV_VAR_BASE_URL,
    ENV_VAR_CLIENT_ID,
    ENV_VAR_CLIENT_SECRET,
    ENV_VAR_ENV,
    get_service_urls,
)
from .manager import TimebackManager
from .provider import (
    AuthCheckResult,
    CaliperPaths,
    EdubridgePaths,
    OneRosterPaths,
    PlatformPaths,
    ResolvedEndpoint,
    TimebackProvider,
)
from .types import (
    AuthCredentials,
    BaseUrlConfig,
    BroadcastFailure,
    BroadcastResult,
    BroadcastSuccess,
    EnvConfig,
    Environment,
    Platform,
    ServicesConfig,
    ServiceUrls,
    TimebackClientConfig,
)

__all__ = [
    "ENV_VAR_AUTH_URL",
    "ENV_VAR_BASE_URL",
    "ENV_VAR_CLIENT_ID",
    "ENV_VAR_CLIENT_SECRET",
    "ENV_VAR_ENV",
    "APIError",
    "AuthCheckResult",
    "AuthCredentials",
    "AuthenticationError",
    "BaseUrlConfig",
    "BroadcastFailure",
    "BroadcastResult",
    "BroadcastResults",
    "BroadcastSuccess",
    "Caliper",
    "CaliperPaths",
    "Edubridge",
    "EdubridgePaths",
    "EnvConfig",
    "Environment",
    "ForbiddenError",
    "FormattedError",
    "NotFoundError",
    "OneRoster",
    "OneRosterPaths",
    "Platform",
    "PlatformPaths",
    "RateLimitError",
    "ResolvedEndpoint",
    "ServerError",
    "ServiceUrls",
    "ServicesConfig",
    "TimebackClient",
    "TimebackClientConfig",
    "TimebackError",
    "TimebackManager",
    "TimebackProvider",
    "ValidationError",
    "__version__",
    "format_api_error",
    "get_service_urls",
    "is_api_error",
]

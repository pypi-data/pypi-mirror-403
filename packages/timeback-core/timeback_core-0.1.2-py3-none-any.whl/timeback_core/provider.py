"""
Re-export TimebackProvider from common infrastructure.

The provider has moved to timeback_common. This module provides
backwards compatibility re-exports.
"""

from timeback_common import (
    AuthCheckResult,
    CaliperPaths,
    EdubridgePaths,
    OneRosterPaths,
    PlatformPaths,
    ResolvedEndpoint,
    ServiceName,
    TimebackProvider,
)

__all__ = [
    "AuthCheckResult",
    "CaliperPaths",
    "EdubridgePaths",
    "OneRosterPaths",
    "PlatformPaths",
    "ResolvedEndpoint",
    "ServiceName",
    "TimebackProvider",
]

"""
ArchiCore Python SDK

Official Python client for the ArchiCore Architecture Analysis API.

Usage:
    from archicore import ArchiCore

    client = ArchiCore(api_key="your-api-key")
    projects = client.projects.list()
"""

from .client import ArchiCore
from .exceptions import (
    ArchiCoreError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)

__version__ = "0.1.0"
__all__ = [
    "ArchiCore",
    "ArchiCoreError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
]

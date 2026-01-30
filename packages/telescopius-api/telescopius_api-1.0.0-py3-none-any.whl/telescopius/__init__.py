"""Telescopius API - Python SDK.

A Python SDK for the Telescopius REST API. Search for astronomical targets,
get observation planning data, and more.
"""

from .client import TelescopiusClient
from .exceptions import (
    TelescopiusError,
    TelescopiusAuthError,
    TelescopiusBadRequestError,
    TelescopiusRateLimitError,
    TelescopiusNotFoundError,
    TelescopiusServerError,
    TelescopiusNetworkError,
)

__version__ = "1.0.0"
__all__ = [
    "TelescopiusClient",
    "TelescopiusError",
    "TelescopiusAuthError",
    "TelescopiusBadRequestError",
    "TelescopiusRateLimitError",
    "TelescopiusNotFoundError",
    "TelescopiusServerError",
    "TelescopiusNetworkError",
]

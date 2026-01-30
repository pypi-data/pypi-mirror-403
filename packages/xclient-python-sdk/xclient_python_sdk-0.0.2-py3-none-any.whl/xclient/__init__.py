"""
XClient Python SDK for accessing XCloud Service API.

This package provides a client library for interacting with the XCloud Service API.
"""

from .api.client import Client, AuthenticatedClient
from .connection_config import (
    ConnectionConfig,
    ProxyTypes,
)
from .exceptions import (
    XClientException,
    TimeoutException,
    NotFoundException,
    AuthenticationException,
    InvalidArgumentException,
    NotEnoughSpaceException,
    RateLimitException,
    APIException,
)
from .task import Task, TaskClient

__all__ = [
    # API
    "Client",
    "AuthenticatedClient",
    # Connection config
    "ConnectionConfig",
    "ProxyTypes",
    # Exceptions
    "XClientException",
    "TimeoutException",
    "NotFoundException",
    "AuthenticationException",
    "InvalidArgumentException",
    "NotEnoughSpaceException",
    "RateLimitException",
    "APIException",
    # Task SDK
    "Task",
    "TaskClient",
]

__version__ = "1.0.0"


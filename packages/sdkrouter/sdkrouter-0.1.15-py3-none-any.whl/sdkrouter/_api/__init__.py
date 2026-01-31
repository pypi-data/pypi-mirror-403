"""
SDKRouter API Client Utilities.

Provides base classes for building tool resources:
- HTTPClientFactory: Creates configured httpx clients
- BaseResource: Base class for sync tool resources
- AsyncBaseResource: Base class for async tool resources

Usage:
    >>> from sdkrouter._api import BaseResource, AsyncBaseResource
    >>>
    >>> class MyResource(BaseResource):
    ...     def __init__(self, config):
    ...         super().__init__(config)
    ...         self._api = SyncMyAPI(self._http_client)
"""

from .client import (
    HTTPClientFactory,
    BaseResource,
    AsyncBaseResource,
)

__all__ = [
    "HTTPClientFactory",
    "BaseResource",
    "AsyncBaseResource",
]

"""API Keys management tool using generated API client."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import httpx

from .._config import SDKConfig

logger = logging.getLogger(__name__)
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncSdkKeysSdkKeysAPI,
    SdkKeysSdkKeysAPI,
)
from .._api.generated.sdk_keys.sdk_keys__api__sdk_keys.models import (
    SDKAPIKeyList,
    SDKAPIKeyDetail,
    SDKAPIKeyCreate,
    SDKAPIKeyCreateRequest,
    PaginatedSDKAPIKeyListList,
)
from .._api.generated.sdk_keys.enums import (
    SDKAPIKeyCreatePermission,
)


class KeysResource(BaseResource):
    """API Keys management tool (sync).

    Uses generated SyncSdkKeysSdkKeysAPI client.

    Example:
        ```python
        from sdkrouter import SDKRouter

        client = SDKRouter(api_key="your-api-key")

        # Create a new key
        new_key = client.keys.create(name="Production Key")
        print(f"New key: {new_key.plain_key}")  # Save this!

        # List all keys
        keys = client.keys.list()
        for key in keys.results:
            print(f"{key.name}: {key.key_prefix}...")

        # Rotate a key
        rotated = client.keys.rotate(key_id)
        print(f"New rotated key: {rotated.plain_key}")
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncSdkKeysSdkKeysAPI(self._http_client)

    def create(
        self,
        name: str,
        *,
        permission: SDKAPIKeyCreatePermission = SDKAPIKeyCreatePermission.WRITE,
        rate_limit_rpm: int | None = None,
        rate_limit_rpd: int | None = None,
        quota_monthly_usd: Decimal | None = None,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        is_test: bool = False,
    ) -> SDKAPIKeyCreate:
        """
        Create a new API key.

        Args:
            name: Human-readable name for the key
            permission: Permission level (read, write, admin)
            rate_limit_rpm: Max requests per minute (None = unlimited)
            rate_limit_rpd: Max requests per day (None = unlimited)
            quota_monthly_usd: Monthly spending limit in USD
            expires_at: When the key expires
            metadata: Additional metadata
            is_test: Create a test key (sk_test_ prefix)

        Returns:
            SDKAPIKeyCreate with key info including `plain_key` (only shown once!)
        """
        logger.debug("Creating API key: name=%s, permission=%s, is_test=%s", name, permission, is_test)
        request = SDKAPIKeyCreateRequest(
            name=name,
            permission=permission,
            rate_limit_rpm=rate_limit_rpm,
            rate_limit_rpd=rate_limit_rpd,
            quota_monthly_usd=str(quota_monthly_usd) if quota_monthly_usd else None,
            expires_at=expires_at.isoformat() if expires_at else None,
            metadata=metadata or {},
            is_test=is_test,
        )
        result = self._api.create(request)
        logger.info("API key created: %s", name)
        return result

    def get(self, key_id: str) -> SDKAPIKeyDetail:
        """Get API key details by ID."""
        return self._api.retrieve(cast(Any, key_id))

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedSDKAPIKeyListList:
        """List your API keys."""
        return self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    def delete(self, key_id: str) -> bool:
        """Deactivate an API key (soft delete)."""
        try:
            logger.debug("Deleting API key: %s", key_id)
            self._api.destroy(cast(Any, key_id))
            logger.info("API key deleted: %s", key_id)
            return True
        except httpx.HTTPStatusError as e:
            logger.warning("API key delete failed for %s: %s", key_id, e)
            return False

    def rotate(self, key_id: str) -> SDKAPIKeyList:
        """
        Rotate an API key (generate new key).

        The old key will stop working immediately.

        Returns:
            SDKAPIKeyList with `plain_key` (the new key - only shown once!)
        """
        logger.debug("Rotating API key: %s", key_id)
        result = self._api.rotate_create(cast(Any, key_id))
        logger.info("API key rotated: %s", key_id)
        return result

    def reactivate(self, key_id: str) -> SDKAPIKeyList:
        """Reactivate a deactivated API key."""
        logger.debug("Reactivating API key: %s", key_id)
        result = self._api.reactivate_create(cast(Any, key_id))
        logger.info("API key reactivated: %s", key_id)
        return result


class AsyncKeysResource(AsyncBaseResource):
    """API Keys management tool (async).

    Uses generated SdkKeysSdkKeysAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SdkKeysSdkKeysAPI(self._http_client)

    async def create(
        self,
        name: str,
        *,
        permission: SDKAPIKeyCreatePermission = SDKAPIKeyCreatePermission.WRITE,
        rate_limit_rpm: int | None = None,
        rate_limit_rpd: int | None = None,
        quota_monthly_usd: Decimal | None = None,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        is_test: bool = False,
    ) -> SDKAPIKeyCreate:
        """Create a new API key."""
        logger.debug("Creating API key: name=%s, permission=%s, is_test=%s", name, permission, is_test)
        request = SDKAPIKeyCreateRequest(
            name=name,
            permission=permission,
            rate_limit_rpm=rate_limit_rpm,
            rate_limit_rpd=rate_limit_rpd,
            quota_monthly_usd=str(quota_monthly_usd) if quota_monthly_usd else None,
            expires_at=expires_at.isoformat() if expires_at else None,
            metadata=metadata or {},
            is_test=is_test,
        )
        result = await self._api.create(request)
        logger.info("API key created: %s", name)
        return result

    async def get(self, key_id: str) -> SDKAPIKeyDetail:
        """Get API key details by ID."""
        return await self._api.retrieve(cast(Any, key_id))

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedSDKAPIKeyListList:
        """List your API keys."""
        return await self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    async def delete(self, key_id: str) -> bool:
        """Deactivate an API key (soft delete)."""
        try:
            logger.debug("Deleting API key: %s", key_id)
            await self._api.destroy(cast(Any, key_id))
            logger.info("API key deleted: %s", key_id)
            return True
        except httpx.HTTPStatusError as e:
            logger.warning("API key delete failed for %s: %s", key_id, e)
            return False

    async def rotate(self, key_id: str) -> SDKAPIKeyList:
        """Rotate an API key (generate new key)."""
        logger.debug("Rotating API key: %s", key_id)
        result = await self._api.rotate_create(cast(Any, key_id))
        logger.info("API key rotated: %s", key_id)
        return result

    async def reactivate(self, key_id: str) -> SDKAPIKeyList:
        """Reactivate a deactivated API key."""
        logger.debug("Reactivating API key: %s", key_id)
        result = await self._api.reactivate_create(cast(Any, key_id))
        logger.info("API key reactivated: %s", key_id)
        return result


__all__ = [
    "KeysResource",
    "AsyncKeysResource",
    # Models
    "SDKAPIKeyList",
    "SDKAPIKeyDetail",
    "SDKAPIKeyCreate",
    "SDKAPIKeyCreateRequest",
    "PaginatedSDKAPIKeyListList",
    # Enums
    "SDKAPIKeyCreatePermission",
]

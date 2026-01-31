"""Proxies tool using generated API client.

Provides proxy management, rotation configurations, assignments,
and health monitoring through the SDKRouter API.
"""

from __future__ import annotations

import logging
from typing import Any

from .._config import SDKConfig
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)

from .._api.client import (
    BaseResource,
    AsyncBaseResource,
)
from .._api.generated.proxies.proxies__api__proxies.sync_client import SyncProxiesProxiesAPI
from .._api.generated.proxies.proxies__api__proxies.client import ProxiesProxiesAPI
from .._api.generated.proxies.proxies__api__proxies.models import (
    # Proxy
    Proxy,
    ProxyRequest,
    PatchedProxyRequest,
    PaginatedProxyList,
    # ProxyAssignment
    ProxyAssignment,
    ProxyAssignmentRequest,
    PatchedProxyAssignmentRequest,
    PaginatedProxyAssignmentList,
    # ProxyRotation
    ProxyRotation,
    ProxyRotationRequest,
    PatchedProxyRotationRequest,
    PaginatedProxyRotationList,
    # ProxyTest
    ProxyTest,
    ProxyTestRequest,
    PatchedProxyTestRequest,
    PaginatedProxyTestList,
)
from .._api.generated.proxies.enums import (
    PatchedProxyRequestProxyType as ProxyType,
    PatchedProxyRequestProxyMode as ProxyMode,
    PatchedProxyRequestStatus as ProxyStatus,
    PatchedProxyTestRequestTestType as ProxyTestType,
)


class ProxiesResource(BaseResource):
    """Proxies tool (sync).

    Provides proxy management with CRUD operations, health monitoring,
    rotation configurations, and assignment tracking.

    Features:
    - Create, update, and delete proxies
    - Filter proxies by country, health status
    - Manage rotation configurations
    - Track proxy assignments to parsers
    - Run connectivity and speed tests

    Example:
        ```python
        client = SDKRouter(api_key="...")

        # List all proxies
        proxies = client.proxies.list()
        for proxy in proxies.results:
            print(f"{proxy.host}:{proxy.port} - {proxy.status}")

        # Get healthy proxies
        healthy = client.proxies.get_healthy()

        # Create a new proxy
        proxy = client.proxies.create(
            host="192.168.1.100",
            port=8080,
            proxy_type="http",
            country="KR",
        )

        # Create rotation config
        rotation = client.proxies.create_rotation(
            name="Korean Proxies",
            allowed_countries=["KR"],
            min_success_rate=95.0,
        )
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncProxiesProxiesAPI(self._http_client)

    # =========================================================================
    # Proxies
    # =========================================================================

    @api_error_handler
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyList:
        """List proxies.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            search: Search term for filtering
            ordering: Field to order by (e.g., "-created_at", "host")

        Returns:
            Paginated list of proxies
        """
        return self._api.proxies_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @api_error_handler
    def get(self, proxy_id: str) -> Proxy:
        """Get proxy details.

        Args:
            proxy_id: Proxy UUID

        Returns:
            Proxy details
        """
        return self._api.proxies_retrieve(proxy_id)

    @api_error_handler
    def create(
        self,
        *,
        host: str,
        port: int,
        proxy_type: str | ProxyType | None = None,
        proxy_mode: str | ProxyMode | None = None,
        username: str | None = None,
        password: str | None = None,
        provider: str | None = None,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        status: str | ProxyStatus | None = None,
        is_active: bool | None = None,
        expires_at: str | None = None,
        max_concurrent_requests: int | None = None,
        requests_per_minute: int | None = None,
        cost_per_gb: str | None = None,
        monthly_cost: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> Proxy:
        """Create a new proxy.

        Args:
            host: Proxy host/IP address
            port: Proxy port (1-65535)
            proxy_type: Type (http, https, socks4, socks5)
            proxy_mode: Mode (static, rotating, mobile)
            username: Authentication username
            password: Authentication password
            provider: Provider reference (UUID)
            country: ISO country code (e.g., "KR", "US")
            region: Region/state
            city: City
            status: Status (active, inactive, testing, failed, banned, maintenance)
            is_active: Whether proxy is active
            expires_at: Expiration date (ISO format)
            max_concurrent_requests: Max concurrent requests limit
            requests_per_minute: Rate limit
            cost_per_gb: Cost per GB of traffic
            monthly_cost: Monthly cost
            metadata: Additional metadata
            config: Proxy configuration (gateway, session format, etc.)

        Returns:
            Created proxy

        Example:
            ```python
            proxy = client.proxies.create(
                host="proxy.example.com",
                port=8080,
                proxy_type="http",
                country="KR",
                username="user",
                password="pass",
            )
            print(f"Created: {proxy.proxy_url}")
            ```
        """
        request = ProxyRequest(
            host=host,
            port=port,
            proxy_type=ProxyType(proxy_type) if isinstance(proxy_type, str) and proxy_type else proxy_type,
            proxy_mode=ProxyMode(proxy_mode) if isinstance(proxy_mode, str) and proxy_mode else proxy_mode,
            username=username,
            password=password,
            provider=provider,
            country=country,
            region=region,
            city=city,
            status=ProxyStatus(status) if isinstance(status, str) and status else status,
            is_active=is_active,
            expires_at=expires_at,
            max_concurrent_requests=max_concurrent_requests,
            requests_per_minute=requests_per_minute,
            cost_per_gb=cost_per_gb,
            monthly_cost=monthly_cost,
            metadata=metadata,
            config=config,
        )
        return self._api.proxies_create(request)

    @api_error_handler
    def update(
        self,
        proxy_id: str,
        *,
        host: str | None = None,
        port: int | None = None,
        proxy_type: str | ProxyType | None = None,
        proxy_mode: str | ProxyMode | None = None,
        username: str | None = None,
        password: str | None = None,
        provider: str | None = None,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        status: str | ProxyStatus | None = None,
        is_active: bool | None = None,
        expires_at: str | None = None,
        max_concurrent_requests: int | None = None,
        requests_per_minute: int | None = None,
        cost_per_gb: str | None = None,
        monthly_cost: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> Proxy:
        """Update a proxy (partial update).

        Args:
            proxy_id: Proxy UUID
            **kwargs: Fields to update (only provided fields are changed)

        Returns:
            Updated proxy
        """
        request = PatchedProxyRequest(
            host=host,
            port=port,
            proxy_type=ProxyType(proxy_type) if isinstance(proxy_type, str) and proxy_type else proxy_type,
            proxy_mode=ProxyMode(proxy_mode) if isinstance(proxy_mode, str) and proxy_mode else proxy_mode,
            username=username,
            password=password,
            provider=provider,
            country=country,
            region=region,
            city=city,
            status=ProxyStatus(status) if isinstance(status, str) and status else status,
            is_active=is_active,
            expires_at=expires_at,
            max_concurrent_requests=max_concurrent_requests,
            requests_per_minute=requests_per_minute,
            cost_per_gb=cost_per_gb,
            monthly_cost=monthly_cost,
            metadata=metadata,
            config=config,
        )
        return self._api.proxies_partial_update(proxy_id, request)

    @api_error_handler
    def delete(self, proxy_id: str) -> bool:
        """Delete a proxy.

        Args:
            proxy_id: Proxy UUID

        Returns:
            True if successful
        """
        self._api.proxies_destroy(proxy_id)
        return True

    @api_error_handler
    def get_healthy(self) -> list[Proxy]:
        """Get healthy proxies.

        Returns proxies that are active, have good success rate,
        and acceptable response time.

        Returns:
            List of healthy proxies
        """
        return self._api.proxies_healthy_retrieve()

    @api_error_handler
    def get_korean(self) -> list[Proxy]:
        """Get Korean proxies.

        Returns proxies with country code 'KR'.

        Returns:
            List of Korean proxies
        """
        return self._api.proxies_korean_retrieve()

    @api_error_handler
    def get_by_country(self, country: str | None = None) -> list[Proxy]:
        """Get proxies by country.

        Args:
            country: ISO country code (e.g., "KR", "US")

        Returns:
            List of proxies for the specified country
        """
        return self._api.proxies_by_country_retrieve()

    @api_error_handler
    def get_performance_stats(self) -> dict[str, Any]:
        """Get overall performance statistics.

        Returns:
            Performance statistics including averages, counts, etc.
        """
        return self._api.proxies_performance_stats_retrieve()

    # =========================================================================
    # Rotations
    # =========================================================================

    @api_error_handler
    def list_rotations(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyRotationList:
        """List rotation configurations.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            search: Search term
            ordering: Field to order by

        Returns:
            Paginated list of rotations
        """
        return self._api.rotations_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @api_error_handler
    def get_rotation(self, rotation_id: str) -> ProxyRotation:
        """Get rotation details.

        Args:
            rotation_id: Rotation UUID

        Returns:
            Rotation details
        """
        return self._api.rotations_retrieve(rotation_id)

    @api_error_handler
    def create_rotation(
        self,
        *,
        name: str,
        parser_ids: dict[str, Any] | None = None,
        rotation_interval_minutes: int | None = None,
        max_requests_per_proxy: int | None = None,
        max_errors_per_proxy: int | None = None,
        allowed_countries: list[str] | dict[str, Any] | None = None,
        allowed_providers: list[str] | dict[str, Any] | None = None,
        min_success_rate: float | None = None,
        max_response_time_ms: int | None = None,
        is_active: bool | None = None,
    ) -> ProxyRotation:
        """Create a rotation configuration.

        Args:
            name: Rotation name
            parser_ids: Parser IDs using this rotation
            rotation_interval_minutes: Minutes between rotations
            max_requests_per_proxy: Max requests before rotation
            max_errors_per_proxy: Max errors before rotation
            allowed_countries: Allowed country codes
            allowed_providers: Allowed provider types
            min_success_rate: Minimum success rate (0-100)
            max_response_time_ms: Maximum response time in ms
            is_active: Whether rotation is active

        Returns:
            Created rotation

        Example:
            ```python
            rotation = client.proxies.create_rotation(
                name="Korean Fast Proxies",
                allowed_countries=["KR"],
                min_success_rate=95.0,
                max_response_time_ms=1000,
            )
            ```
        """
        request = ProxyRotationRequest(
            name=name,
            parser_ids=parser_ids,
            rotation_interval_minutes=rotation_interval_minutes,
            max_requests_per_proxy=max_requests_per_proxy,
            max_errors_per_proxy=max_errors_per_proxy,
            allowed_countries=allowed_countries if isinstance(allowed_countries, dict) else ({"codes": allowed_countries} if allowed_countries else None),
            allowed_providers=allowed_providers if isinstance(allowed_providers, dict) else ({"types": allowed_providers} if allowed_providers else None),
            min_success_rate=min_success_rate,
            max_response_time_ms=max_response_time_ms,
            is_active=is_active,
        )
        return self._api.rotations_create(request)

    @api_error_handler
    def update_rotation(
        self,
        rotation_id: str,
        *,
        name: str | None = None,
        parser_ids: dict[str, Any] | None = None,
        rotation_interval_minutes: int | None = None,
        max_requests_per_proxy: int | None = None,
        max_errors_per_proxy: int | None = None,
        allowed_countries: list[str] | dict[str, Any] | None = None,
        allowed_providers: list[str] | dict[str, Any] | None = None,
        min_success_rate: float | None = None,
        max_response_time_ms: int | None = None,
        is_active: bool | None = None,
    ) -> ProxyRotation:
        """Update a rotation configuration (partial update).

        Args:
            rotation_id: Rotation UUID
            **kwargs: Fields to update

        Returns:
            Updated rotation
        """
        request = PatchedProxyRotationRequest(
            name=name,
            parser_ids=parser_ids,
            rotation_interval_minutes=rotation_interval_minutes,
            max_requests_per_proxy=max_requests_per_proxy,
            max_errors_per_proxy=max_errors_per_proxy,
            allowed_countries=allowed_countries if isinstance(allowed_countries, dict) else ({"codes": allowed_countries} if allowed_countries else None),
            allowed_providers=allowed_providers if isinstance(allowed_providers, dict) else ({"types": allowed_providers} if allowed_providers else None),
            min_success_rate=min_success_rate,
            max_response_time_ms=max_response_time_ms,
            is_active=is_active,
        )
        return self._api.rotations_partial_update(rotation_id, request)

    @api_error_handler
    def delete_rotation(self, rotation_id: str) -> bool:
        """Delete a rotation configuration.

        Args:
            rotation_id: Rotation UUID

        Returns:
            True if successful
        """
        self._api.rotations_destroy(rotation_id)
        return True

    @api_error_handler
    def get_available_proxies_for_rotation(self, rotation_id: str) -> list[Proxy]:
        """Get proxies matching rotation criteria.

        Args:
            rotation_id: Rotation UUID

        Returns:
            List of proxies matching the rotation's criteria
        """
        return self._api.rotations_available_proxies_retrieve(rotation_id)

    # =========================================================================
    # Assignments
    # =========================================================================

    @api_error_handler
    def list_assignments(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyAssignmentList:
        """List proxy assignments.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            search: Search term
            ordering: Field to order by

        Returns:
            Paginated list of assignments
        """
        return self._api.assignments_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @api_error_handler
    def get_assignment(self, assignment_id: str) -> ProxyAssignment:
        """Get assignment details.

        Args:
            assignment_id: Assignment UUID

        Returns:
            Assignment details
        """
        return self._api.assignments_retrieve(assignment_id)

    @api_error_handler
    def create_assignment(
        self,
        *,
        proxy: str,
        parser_id: str,
        session_id: str | None = None,
        is_active: bool | None = None,
        priority: int | None = None,
    ) -> ProxyAssignment:
        """Create a proxy assignment.

        Args:
            proxy: Proxy UUID
            parser_id: Parser ID using this proxy
            session_id: Session ID if applicable
            is_active: Whether assignment is active
            priority: Assignment priority (1-10)

        Returns:
            Created assignment
        """
        request = ProxyAssignmentRequest(
            proxy=proxy,
            parser_id=parser_id,
            session_id=session_id,
            is_active=is_active,
            priority=priority,
        )
        return self._api.assignments_create(request)

    @api_error_handler
    def update_assignment(
        self,
        assignment_id: str,
        *,
        proxy: str | None = None,
        parser_id: str | None = None,
        session_id: str | None = None,
        is_active: bool | None = None,
        priority: int | None = None,
    ) -> ProxyAssignment:
        """Update an assignment (partial update).

        Args:
            assignment_id: Assignment UUID
            **kwargs: Fields to update

        Returns:
            Updated assignment
        """
        request = PatchedProxyAssignmentRequest(
            proxy=proxy,
            parser_id=parser_id,
            session_id=session_id,
            is_active=is_active,
            priority=priority,
        )
        return self._api.assignments_partial_update(assignment_id, request)

    @api_error_handler
    def delete_assignment(self, assignment_id: str) -> bool:
        """Delete an assignment.

        Args:
            assignment_id: Assignment UUID

        Returns:
            True if successful
        """
        self._api.assignments_destroy(assignment_id)
        return True

    @api_error_handler
    def get_active_assignments(self) -> list[ProxyAssignment]:
        """Get active assignments.

        Returns:
            List of active assignments
        """
        return self._api.assignments_active_retrieve()

    # =========================================================================
    # Tests
    # =========================================================================

    @api_error_handler
    def list_tests(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyTestList:
        """List proxy tests.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            search: Search term
            ordering: Field to order by

        Returns:
            Paginated list of tests
        """
        return self._api.tests_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @api_error_handler
    def get_test(self, test_id: str) -> ProxyTest:
        """Get test details.

        Args:
            test_id: Test UUID

        Returns:
            Test details
        """
        return self._api.tests_retrieve(test_id)

    @api_error_handler
    def create_test(
        self,
        *,
        proxy: str,
        test_url: str | None = None,
        test_type: str | ProxyTestType | None = None,
    ) -> ProxyTest:
        """Create and run a proxy test.

        Args:
            proxy: Proxy UUID
            test_url: URL to test against
            test_type: Test type (connectivity, speed, anonymity, geolocation)

        Returns:
            Test result

        Example:
            ```python
            test = client.proxies.create_test(
                proxy="uuid-here",
                test_type="connectivity",
            )
            if test.is_successful:
                print(f"Response time: {test.response_time_ms}ms")
            ```
        """
        request = ProxyTestRequest(
            proxy=proxy,
            test_url=test_url,
            test_type=ProxyTestType(test_type) if isinstance(test_type, str) and test_type else test_type,
        )
        return self._api.tests_create(request)

    @api_error_handler
    def delete_test(self, test_id: str) -> bool:
        """Delete a test record.

        Args:
            test_id: Test UUID

        Returns:
            True if successful
        """
        self._api.tests_destroy(test_id)
        return True


class AsyncProxiesResource(AsyncBaseResource):
    """Proxies tool (async).

    Async version of ProxiesResource for use in async contexts.

    Example:
        ```python
        client = AsyncSDKRouter(api_key="...")

        # List all proxies
        proxies = await client.proxies.list()

        # Get healthy proxies
        healthy = await client.proxies.get_healthy()

        # Create a new proxy
        proxy = await client.proxies.create(
            host="192.168.1.100",
            port=8080,
            proxy_type="http",
        )
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = ProxiesProxiesAPI(self._http_client)

    # =========================================================================
    # Proxies
    # =========================================================================

    @async_api_error_handler
    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyList:
        """List proxies."""
        return await self._api.proxies_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @async_api_error_handler
    async def get(self, proxy_id: str) -> Proxy:
        """Get proxy details."""
        return await self._api.proxies_retrieve(proxy_id)

    @async_api_error_handler
    async def create(
        self,
        *,
        host: str,
        port: int,
        proxy_type: str | ProxyType | None = None,
        proxy_mode: str | ProxyMode | None = None,
        username: str | None = None,
        password: str | None = None,
        provider: str | None = None,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        status: str | ProxyStatus | None = None,
        is_active: bool | None = None,
        expires_at: str | None = None,
        max_concurrent_requests: int | None = None,
        requests_per_minute: int | None = None,
        cost_per_gb: str | None = None,
        monthly_cost: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> Proxy:
        """Create a new proxy."""
        request = ProxyRequest(
            host=host,
            port=port,
            proxy_type=ProxyType(proxy_type) if isinstance(proxy_type, str) and proxy_type else proxy_type,
            proxy_mode=ProxyMode(proxy_mode) if isinstance(proxy_mode, str) and proxy_mode else proxy_mode,
            username=username,
            password=password,
            provider=provider,
            country=country,
            region=region,
            city=city,
            status=ProxyStatus(status) if isinstance(status, str) and status else status,
            is_active=is_active,
            expires_at=expires_at,
            max_concurrent_requests=max_concurrent_requests,
            requests_per_minute=requests_per_minute,
            cost_per_gb=cost_per_gb,
            monthly_cost=monthly_cost,
            metadata=metadata,
            config=config,
        )
        return await self._api.proxies_create(request)

    @async_api_error_handler
    async def update(
        self,
        proxy_id: str,
        *,
        host: str | None = None,
        port: int | None = None,
        proxy_type: str | ProxyType | None = None,
        proxy_mode: str | ProxyMode | None = None,
        username: str | None = None,
        password: str | None = None,
        provider: str | None = None,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        status: str | ProxyStatus | None = None,
        is_active: bool | None = None,
        expires_at: str | None = None,
        max_concurrent_requests: int | None = None,
        requests_per_minute: int | None = None,
        cost_per_gb: str | None = None,
        monthly_cost: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> Proxy:
        """Update a proxy (partial update)."""
        request = PatchedProxyRequest(
            host=host,
            port=port,
            proxy_type=ProxyType(proxy_type) if isinstance(proxy_type, str) and proxy_type else proxy_type,
            proxy_mode=ProxyMode(proxy_mode) if isinstance(proxy_mode, str) and proxy_mode else proxy_mode,
            username=username,
            password=password,
            provider=provider,
            country=country,
            region=region,
            city=city,
            status=ProxyStatus(status) if isinstance(status, str) and status else status,
            is_active=is_active,
            expires_at=expires_at,
            max_concurrent_requests=max_concurrent_requests,
            requests_per_minute=requests_per_minute,
            cost_per_gb=cost_per_gb,
            monthly_cost=monthly_cost,
            metadata=metadata,
            config=config,
        )
        return await self._api.proxies_partial_update(proxy_id, request)

    @async_api_error_handler
    async def delete(self, proxy_id: str) -> bool:
        """Delete a proxy."""
        await self._api.proxies_destroy(proxy_id)
        return True

    @async_api_error_handler
    async def get_healthy(self) -> list[Proxy]:
        """Get healthy proxies."""
        return await self._api.proxies_healthy_retrieve()

    @async_api_error_handler
    async def get_korean(self) -> list[Proxy]:
        """Get Korean proxies."""
        return await self._api.proxies_korean_retrieve()

    @async_api_error_handler
    async def get_by_country(self, country: str | None = None) -> list[Proxy]:
        """Get proxies by country."""
        return await self._api.proxies_by_country_retrieve()

    @async_api_error_handler
    async def get_performance_stats(self) -> dict[str, Any]:
        """Get overall performance statistics."""
        return await self._api.proxies_performance_stats_retrieve()

    # =========================================================================
    # Rotations
    # =========================================================================

    @async_api_error_handler
    async def list_rotations(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyRotationList:
        """List rotation configurations."""
        return await self._api.rotations_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @async_api_error_handler
    async def get_rotation(self, rotation_id: str) -> ProxyRotation:
        """Get rotation details."""
        return await self._api.rotations_retrieve(rotation_id)

    @async_api_error_handler
    async def create_rotation(
        self,
        *,
        name: str,
        parser_ids: dict[str, Any] | None = None,
        rotation_interval_minutes: int | None = None,
        max_requests_per_proxy: int | None = None,
        max_errors_per_proxy: int | None = None,
        allowed_countries: list[str] | dict[str, Any] | None = None,
        allowed_providers: list[str] | dict[str, Any] | None = None,
        min_success_rate: float | None = None,
        max_response_time_ms: int | None = None,
        is_active: bool | None = None,
    ) -> ProxyRotation:
        """Create a rotation configuration."""
        request = ProxyRotationRequest(
            name=name,
            parser_ids=parser_ids,
            rotation_interval_minutes=rotation_interval_minutes,
            max_requests_per_proxy=max_requests_per_proxy,
            max_errors_per_proxy=max_errors_per_proxy,
            allowed_countries=allowed_countries if isinstance(allowed_countries, dict) else ({"codes": allowed_countries} if allowed_countries else None),
            allowed_providers=allowed_providers if isinstance(allowed_providers, dict) else ({"types": allowed_providers} if allowed_providers else None),
            min_success_rate=min_success_rate,
            max_response_time_ms=max_response_time_ms,
            is_active=is_active,
        )
        return await self._api.rotations_create(request)

    @async_api_error_handler
    async def update_rotation(
        self,
        rotation_id: str,
        *,
        name: str | None = None,
        parser_ids: dict[str, Any] | None = None,
        rotation_interval_minutes: int | None = None,
        max_requests_per_proxy: int | None = None,
        max_errors_per_proxy: int | None = None,
        allowed_countries: list[str] | dict[str, Any] | None = None,
        allowed_providers: list[str] | dict[str, Any] | None = None,
        min_success_rate: float | None = None,
        max_response_time_ms: int | None = None,
        is_active: bool | None = None,
    ) -> ProxyRotation:
        """Update a rotation configuration (partial update)."""
        request = PatchedProxyRotationRequest(
            name=name,
            parser_ids=parser_ids,
            rotation_interval_minutes=rotation_interval_minutes,
            max_requests_per_proxy=max_requests_per_proxy,
            max_errors_per_proxy=max_errors_per_proxy,
            allowed_countries=allowed_countries if isinstance(allowed_countries, dict) else ({"codes": allowed_countries} if allowed_countries else None),
            allowed_providers=allowed_providers if isinstance(allowed_providers, dict) else ({"types": allowed_providers} if allowed_providers else None),
            min_success_rate=min_success_rate,
            max_response_time_ms=max_response_time_ms,
            is_active=is_active,
        )
        return await self._api.rotations_partial_update(rotation_id, request)

    @async_api_error_handler
    async def delete_rotation(self, rotation_id: str) -> bool:
        """Delete a rotation configuration."""
        await self._api.rotations_destroy(rotation_id)
        return True

    @async_api_error_handler
    async def get_available_proxies_for_rotation(self, rotation_id: str) -> list[Proxy]:
        """Get proxies matching rotation criteria."""
        return await self._api.rotations_available_proxies_retrieve(rotation_id)

    # =========================================================================
    # Assignments
    # =========================================================================

    @async_api_error_handler
    async def list_assignments(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyAssignmentList:
        """List proxy assignments."""
        return await self._api.assignments_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @async_api_error_handler
    async def get_assignment(self, assignment_id: str) -> ProxyAssignment:
        """Get assignment details."""
        return await self._api.assignments_retrieve(assignment_id)

    @async_api_error_handler
    async def create_assignment(
        self,
        *,
        proxy: str,
        parser_id: str,
        session_id: str | None = None,
        is_active: bool | None = None,
        priority: int | None = None,
    ) -> ProxyAssignment:
        """Create a proxy assignment."""
        request = ProxyAssignmentRequest(
            proxy=proxy,
            parser_id=parser_id,
            session_id=session_id,
            is_active=is_active,
            priority=priority,
        )
        return await self._api.assignments_create(request)

    @async_api_error_handler
    async def update_assignment(
        self,
        assignment_id: str,
        *,
        proxy: str | None = None,
        parser_id: str | None = None,
        session_id: str | None = None,
        is_active: bool | None = None,
        priority: int | None = None,
    ) -> ProxyAssignment:
        """Update an assignment (partial update)."""
        request = PatchedProxyAssignmentRequest(
            proxy=proxy,
            parser_id=parser_id,
            session_id=session_id,
            is_active=is_active,
            priority=priority,
        )
        return await self._api.assignments_partial_update(assignment_id, request)

    @async_api_error_handler
    async def delete_assignment(self, assignment_id: str) -> bool:
        """Delete an assignment."""
        await self._api.assignments_destroy(assignment_id)
        return True

    @async_api_error_handler
    async def get_active_assignments(self) -> list[ProxyAssignment]:
        """Get active assignments."""
        return await self._api.assignments_active_retrieve()

    # =========================================================================
    # Tests
    # =========================================================================

    @async_api_error_handler
    async def list_tests(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        ordering: str | None = None,
    ) -> PaginatedProxyTestList:
        """List proxy tests."""
        return await self._api.tests_list(
            page=page,
            page_size=page_size,
            search=search,
            ordering=ordering,
        )

    @async_api_error_handler
    async def get_test(self, test_id: str) -> ProxyTest:
        """Get test details."""
        return await self._api.tests_retrieve(test_id)

    @async_api_error_handler
    async def create_test(
        self,
        *,
        proxy: str,
        test_url: str | None = None,
        test_type: str | ProxyTestType | None = None,
    ) -> ProxyTest:
        """Create and run a proxy test."""
        request = ProxyTestRequest(
            proxy=proxy,
            test_url=test_url,
            test_type=ProxyTestType(test_type) if isinstance(test_type, str) and test_type else test_type,
        )
        return await self._api.tests_create(request)

    @async_api_error_handler
    async def delete_test(self, test_id: str) -> bool:
        """Delete a test record."""
        await self._api.tests_destroy(test_id)
        return True


__all__ = [
    # Resources
    "ProxiesResource",
    "AsyncProxiesResource",
    # Proxy models
    "Proxy",
    "ProxyRequest",
    "PatchedProxyRequest",
    "PaginatedProxyList",
    # Assignment models
    "ProxyAssignment",
    "ProxyAssignmentRequest",
    "PatchedProxyAssignmentRequest",
    "PaginatedProxyAssignmentList",
    # Rotation models
    "ProxyRotation",
    "ProxyRotationRequest",
    "PatchedProxyRotationRequest",
    "PaginatedProxyRotationList",
    # Test models
    "ProxyTest",
    "ProxyTestRequest",
    "PatchedProxyTestRequest",
    "PaginatedProxyTestList",
    # Enums
    "ProxyType",
    "ProxyMode",
    "ProxyStatus",
    "ProxyTestType",
]

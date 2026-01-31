from __future__ import annotations

import httpx

from .models import (
    PaginatedProxyAssignmentList,
    PaginatedProxyList,
    PaginatedProxyRotationList,
    PaginatedProxyTestList,
    PatchedProxyAssignmentRequest,
    PatchedProxyRequest,
    PatchedProxyRotationRequest,
    PatchedProxyTestRequest,
    Proxy,
    ProxyAssignment,
    ProxyAssignmentRequest,
    ProxyRequest,
    ProxyRotation,
    ProxyRotationRequest,
    ProxyTest,
    ProxyTestRequest,
)


class SyncProxiesProxiesAPI:
    """Synchronous API endpoints for Proxies."""

    def __init__(self, client: httpx.Client):
        """Initialize sync sub-client with shared httpx client."""
        self._client = client

    def assignments_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedProxyAssignmentList]:
        """
        ViewSet for ProxyAssignment.
        """
        url = "/api/proxies/assignments/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedProxyAssignmentList.model_validate(response.json())


    def assignments_create(self, data: ProxyAssignmentRequest) -> ProxyAssignment:
        """
        ViewSet for ProxyAssignment.
        """
        url = "/api/proxies/assignments/"
        response = self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyAssignment.model_validate(response.json())


    def assignments_retrieve(self, id: str) -> ProxyAssignment:
        """
        ViewSet for ProxyAssignment.
        """
        url = f"/api/proxies/assignments/{id}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyAssignment.model_validate(response.json())


    def assignments_update(self, id: str, data: ProxyAssignmentRequest) -> ProxyAssignment:
        """
        ViewSet for ProxyAssignment.
        """
        url = f"/api/proxies/assignments/{id}/"
        response = self._client.put(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyAssignment.model_validate(response.json())


    def assignments_partial_update(
        self,
        id: str,
        data: PatchedProxyAssignmentRequest | None = None,
    ) -> ProxyAssignment:
        """
        ViewSet for ProxyAssignment.
        """
        url = f"/api/proxies/assignments/{id}/"
        _json = data.model_dump(exclude_unset=True) if data else None
        response = self._client.patch(url, json=_json)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyAssignment.model_validate(response.json())


    def assignments_destroy(self, id: str) -> None:
        """
        ViewSet for ProxyAssignment.
        """
        url = f"/api/proxies/assignments/{id}/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def assignments_active_retrieve(self) -> ProxyAssignment:
        """
        Get active assignments

        Get active assignments.
        """
        url = "/api/proxies/assignments/active/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyAssignment.model_validate(response.json())


    def proxies_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedProxyList]:
        """
        ViewSet for Proxy.
        """
        url = "/api/proxies/proxies/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedProxyList.model_validate(response.json())


    def proxies_create(self, data: ProxyRequest) -> Proxy:
        """
        ViewSet for Proxy.
        """
        url = "/api/proxies/proxies/"
        response = self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_retrieve(self, id: str) -> Proxy:
        """
        ViewSet for Proxy.
        """
        url = f"/api/proxies/proxies/{id}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_update(self, id: str, data: ProxyRequest) -> Proxy:
        """
        ViewSet for Proxy.
        """
        url = f"/api/proxies/proxies/{id}/"
        response = self._client.put(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_partial_update(
        self,
        id: str,
        data: PatchedProxyRequest | None = None,
    ) -> Proxy:
        """
        ViewSet for Proxy.
        """
        url = f"/api/proxies/proxies/{id}/"
        _json = data.model_dump(exclude_unset=True) if data else None
        response = self._client.patch(url, json=_json)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_destroy(self, id: str) -> None:
        """
        ViewSet for Proxy.
        """
        url = f"/api/proxies/proxies/{id}/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def proxies_by_country_retrieve(self) -> Proxy:
        """
        Get proxies by country

        Get proxies by country code.
        """
        url = "/api/proxies/proxies/by_country/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_healthy_retrieve(self) -> Proxy:
        """
        Get healthy proxies

        Get healthy proxies.
        """
        url = "/api/proxies/proxies/healthy/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_korean_retrieve(self) -> Proxy:
        """
        Get Korean proxies

        Get Korean proxies.
        """
        url = "/api/proxies/proxies/korean/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def proxies_performance_stats_retrieve(self) -> Proxy:
        """
        Get performance stats

        Get overall performance statistics.
        """
        url = "/api/proxies/proxies/performance_stats/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Proxy.model_validate(response.json())


    def rotations_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedProxyRotationList]:
        """
        ViewSet for ProxyRotation.
        """
        url = "/api/proxies/rotations/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedProxyRotationList.model_validate(response.json())


    def rotations_create(self, data: ProxyRotationRequest) -> ProxyRotation:
        """
        ViewSet for ProxyRotation.
        """
        url = "/api/proxies/rotations/"
        response = self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyRotation.model_validate(response.json())


    def rotations_retrieve(self, id: str) -> ProxyRotation:
        """
        ViewSet for ProxyRotation.
        """
        url = f"/api/proxies/rotations/{id}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyRotation.model_validate(response.json())


    def rotations_update(self, id: str, data: ProxyRotationRequest) -> ProxyRotation:
        """
        ViewSet for ProxyRotation.
        """
        url = f"/api/proxies/rotations/{id}/"
        response = self._client.put(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyRotation.model_validate(response.json())


    def rotations_partial_update(
        self,
        id: str,
        data: PatchedProxyRotationRequest | None = None,
    ) -> ProxyRotation:
        """
        ViewSet for ProxyRotation.
        """
        url = f"/api/proxies/rotations/{id}/"
        _json = data.model_dump(exclude_unset=True) if data else None
        response = self._client.patch(url, json=_json)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyRotation.model_validate(response.json())


    def rotations_destroy(self, id: str) -> None:
        """
        ViewSet for ProxyRotation.
        """
        url = f"/api/proxies/rotations/{id}/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def rotations_available_proxies_retrieve(self, id: str) -> ProxyRotation:
        """
        Get available proxies for rotation

        Get proxies matching the rotation criteria.
        """
        url = f"/api/proxies/rotations/{id}/available_proxies/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyRotation.model_validate(response.json())


    def tests_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedProxyTestList]:
        """
        ViewSet for ProxyTest.
        """
        url = "/api/proxies/tests/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedProxyTestList.model_validate(response.json())


    def tests_create(self, data: ProxyTestRequest) -> ProxyTest:
        """
        ViewSet for ProxyTest.
        """
        url = "/api/proxies/tests/"
        response = self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyTest.model_validate(response.json())


    def tests_retrieve(self, id: str) -> ProxyTest:
        """
        ViewSet for ProxyTest.
        """
        url = f"/api/proxies/tests/{id}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyTest.model_validate(response.json())


    def tests_update(self, id: str, data: ProxyTestRequest) -> ProxyTest:
        """
        ViewSet for ProxyTest.
        """
        url = f"/api/proxies/tests/{id}/"
        response = self._client.put(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyTest.model_validate(response.json())


    def tests_partial_update(
        self,
        id: str,
        data: PatchedProxyTestRequest | None = None,
    ) -> ProxyTest:
        """
        ViewSet for ProxyTest.
        """
        url = f"/api/proxies/tests/{id}/"
        _json = data.model_dump(exclude_unset=True) if data else None
        response = self._client.patch(url, json=_json)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProxyTest.model_validate(response.json())


    def tests_destroy(self, id: str) -> None:
        """
        ViewSet for ProxyTest.
        """
        url = f"/api/proxies/tests/{id}/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )



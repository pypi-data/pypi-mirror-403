from __future__ import annotations

import httpx

from .models import (
    CapabilitiesListResponse,
    CategoriesListResponse,
    CostCalculationRequestRequest,
    CostCalculationResponse,
    LLMModelDetail,
    PaginatedLLMModelListList,
    PresetsListResponse,
    ProvidersResponse,
    ResolveRequestRequest,
    ResolveResponse,
    StatsResponse,
)


class SyncModelsLlmModelsAPI:
    """Synchronous API endpoints for Llm Models."""

    def __init__(self, client: httpx.Client):
        """Initialize sync sub-client with shared httpx client."""
        self._client = client

    def list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedLLMModelListList]:
        """
        List models

        Get list of available LLM models with filtering.
        """
        url = "/api/llm_models/"
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
        return PaginatedLLMModelListList.model_validate(response.json())


    def retrieve(self, model_id: str) -> LLMModelDetail:
        """
        Get model details

        Get detailed information about a specific model.
        """
        url = f"/api/llm_models/{model_id}/"
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
        return LLMModelDetail.model_validate(response.json())


    def calculate_cost_create(
        self,
        model_id: str,
        data: CostCalculationRequestRequest,
    ) -> CostCalculationResponse:
        """
        Calculate cost

        Calculate cost for a request.
        """
        url = f"/api/llm_models/{model_id}/calculate-cost/"
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
        return CostCalculationResponse.model_validate(response.json())


    def capabilities_retrieve(self) -> list[CapabilitiesListResponse]:
        """
        List capabilities

        Get list of valid capability modifiers.
        """
        url = "/api/llm_models/capabilities/"
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
        return CapabilitiesListResponse.model_validate(response.json())


    def categories_retrieve(self) -> list[CategoriesListResponse]:
        """
        List categories

        Get list of available model categories.
        """
        url = "/api/llm_models/categories/"
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
        return CategoriesListResponse.model_validate(response.json())


    def presets_retrieve(self) -> list[PresetsListResponse]:
        """
        List presets

        Get list of available model presets (tiers).
        """
        url = "/api/llm_models/presets/"
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
        return PresetsListResponse.model_validate(response.json())


    def providers_retrieve(self) -> ProvidersResponse:
        """
        List providers

        Get list of available providers.
        """
        url = "/api/llm_models/providers/"
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
        return ProvidersResponse.model_validate(response.json())


    def resolve_create(self, data: ResolveRequestRequest) -> ResolveResponse:
        """
        Resolve model alias

        Resolve an alias like @cheap or @smart+vision to a specific model.
        """
        url = "/api/llm_models/resolve/"
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
        return ResolveResponse.model_validate(response.json())


    def stats_retrieve(self) -> StatsResponse:
        """
        Get statistics

        Get model statistics.
        """
        url = "/api/llm_models/stats/"
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
        return StatsResponse.model_validate(response.json())



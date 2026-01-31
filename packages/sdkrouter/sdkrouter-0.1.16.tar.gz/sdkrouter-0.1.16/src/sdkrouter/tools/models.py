"""LLM Models tool using generated API client."""

from typing import Optional

from .._config import SDKConfig
from ..exceptions import api_error_handler, async_api_error_handler
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncModelsLlmModelsAPI,
    ModelsLlmModelsAPI,
)
from .._api.generated.models.models__api__llm_models.models import (
    LLMModelList,
    LLMModelDetail,
    PaginatedLLMModelListList,
    ProvidersResponse,
    StatsResponse,
    CostCalculationRequestRequest,
    CostCalculationResponse,
)


class ModelsResource(BaseResource):
    """LLM Models tool (sync).

    Uses generated SyncModelsLlmModelsAPI client.

    Example:
        ```python
        from sdkrouter import SDKRouter

        client = SDKRouter(api_key="your-api-key")

        # List all models with pagination
        models = client.models.list(page=1, page_size=20)
        for model in models.results:
            print(f"{model.model_id}: {model.name}")

        # Get model details
        model = client.models.get("openai/gpt-4o")
        print(f"Context: {model.context_length} tokens")

        # Calculate cost
        cost = client.models.calculate_cost(
            "openai/gpt-4o",
            input_tokens=1000,
            output_tokens=500
        )
        print(f"Cost: ${cost.total_cost_usd}")

        # Get providers list
        providers = client.models.providers()
        for p in providers.providers:
            print(f"{p.name}: {p.model_count} models")

        # Get statistics
        stats = client.models.stats()
        print(f"Total models: {stats.total_models}")
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncModelsLlmModelsAPI(self._http_client)

    @api_error_handler
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedLLMModelListList:
        """
        List available LLM models with pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of results per page

        Returns:
            Paginated list of LLM models.
        """
        return self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    @api_error_handler
    def get(self, model_id: str) -> LLMModelDetail:
        """
        Get detailed information about a specific model.

        Args:
            model_id: Model identifier (e.g., 'openai/gpt-4o')

        Returns:
            Model details including pricing, capabilities, etc.
        """
        return self._api.retrieve(model_id)

    @api_error_handler
    def calculate_cost(
        self,
        model_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> CostCalculationResponse:
        """
        Calculate cost for a request.

        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost calculation result.
        """
        request = CostCalculationRequestRequest(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        return self._api.calculate_cost_create(model_id, request)

    @api_error_handler
    def providers(self) -> ProvidersResponse:
        """
        Get list of available providers.

        Returns:
            List of providers with model counts.
        """
        return self._api.providers_retrieve()

    @api_error_handler
    def stats(self) -> StatsResponse:
        """
        Get model statistics.

        Returns:
            Statistics about available models.
        """
        return self._api.stats_retrieve()


class AsyncModelsResource(AsyncBaseResource):
    """LLM Models tool (async).

    Uses generated ModelsLlmModelsAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = ModelsLlmModelsAPI(self._http_client)

    @async_api_error_handler
    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedLLMModelListList:
        """List available LLM models with pagination."""
        return await self._api.list(page=page, page_size=page_size)  # type: ignore[return-value]

    @async_api_error_handler
    async def get(self, model_id: str) -> LLMModelDetail:
        """Get detailed information about a specific model."""
        return await self._api.retrieve(model_id)

    @async_api_error_handler
    async def calculate_cost(
        self,
        model_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> CostCalculationResponse:
        """Calculate cost for a request."""
        request = CostCalculationRequestRequest(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        return await self._api.calculate_cost_create(model_id, request)

    @async_api_error_handler
    async def providers(self) -> ProvidersResponse:
        """Get list of available providers."""
        return await self._api.providers_retrieve()

    @async_api_error_handler
    async def stats(self) -> StatsResponse:
        """Get model statistics."""
        return await self._api.stats_retrieve()


__all__ = [
    "ModelsResource",
    "AsyncModelsResource",
    # Models
    "LLMModelList",
    "LLMModelDetail",
    "PaginatedLLMModelListList",
    "ProvidersResponse",
    "StatsResponse",
    "CostCalculationRequestRequest",
    "CostCalculationResponse",
]

"""Embeddings tool for SDKRouter."""

from typing import Literal

from pydantic import BaseModel

from .._config import SDKConfig
from .._api.client import BaseResource, AsyncBaseResource
from ..exceptions import handle_api_errors, async_api_error_handler


class EmbeddingUsage(BaseModel):
    """Token usage for embedding request."""

    prompt_tokens: int
    total_tokens: int


class EmbeddingData(BaseModel):
    """Single embedding data."""

    object: Literal["embedding"] = "embedding"
    index: int
    embedding: list[float]


class EmbeddingResponse(BaseModel):
    """Response from embedding request."""

    object: Literal["list"] = "list"
    data: list[EmbeddingData]
    model: str
    usage: EmbeddingUsage


class EmbeddingsResource(BaseResource):
    """Embeddings tool (sync).

    Provides text embedding capabilities via OpenAI-compatible API.
    Uses FastAPI server (openai_url) for requests.

    Example:
        ```python
        from sdkrouter import SDKRouter

        client = SDKRouter(api_key="your-api-key")

        # Single text embedding
        result = client.embeddings.create("Hello world")
        print(f"Dimensions: {len(result.data[0].embedding)}")

        # Batch embeddings
        texts = ["Hello", "World", "AI"]
        result = client.embeddings.create(texts)
        for i, item in enumerate(result.data):
            print(f"Text {i}: {len(item.embedding)} dimensions")
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config, use_llm_url=True)

    def create(
        self,
        input: str | list[str],
        *,
        model: str = "openai/text-embedding-3-small",
        encoding_format: Literal["float", "base64"] = "float",
        user: str | None = None,
    ) -> EmbeddingResponse:
        """
        Create embeddings for the given input.

        Args:
            input: Text string or list of text strings to embed
            model: Embedding model to use (default: openai/text-embedding-3-small)
            encoding_format: Output format - "float" or "base64" (default: "float")
            user: Optional user identifier for tracking

        Returns:
            EmbeddingResponse with embeddings for each input text

        Example:
            ```python
            # Single text
            result = client.embeddings.create("Hello world")
            embedding = result.data[0].embedding

            # Multiple texts
            result = client.embeddings.create(["Hello", "World"])
            for item in result.data:
                print(len(item.embedding))
            ```
        """
        data = {
            "model": model,
            "input": input,
            "encoding_format": encoding_format,
        }

        if user:
            data["user"] = user

        with handle_api_errors():
            response = self._http_client.post("/embeddings", json=data)
            response.raise_for_status()
            return EmbeddingResponse.model_validate(response.json())


class AsyncEmbeddingsResource(AsyncBaseResource):
    """Embeddings tool (async).

    Async version of EmbeddingsResource.
    Uses FastAPI server (openai_url) for requests.

    Example:
        ```python
        from sdkrouter import AsyncSDKRouter

        client = AsyncSDKRouter(api_key="your-api-key")

        # Single text embedding
        result = await client.embeddings.create("Hello world")
        print(f"Dimensions: {len(result.data[0].embedding)}")
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config, use_llm_url=True)

    @async_api_error_handler
    async def create(
        self,
        input: str | list[str],
        *,
        model: str = "openai/text-embedding-3-small",
        encoding_format: Literal["float", "base64"] = "float",
        user: str | None = None,
    ) -> EmbeddingResponse:
        """
        Create embeddings for the given input (async).

        Args:
            input: Text string or list of text strings to embed
            model: Embedding model to use (default: openai/text-embedding-3-small)
            encoding_format: Output format - "float" or "base64" (default: "float")
            user: Optional user identifier for tracking

        Returns:
            EmbeddingResponse with embeddings for each input text
        """
        data = {
            "model": model,
            "input": input,
            "encoding_format": encoding_format,
        }

        if user:
            data["user"] = user

        response = await self._http_client.post("/embeddings", json=data)
        response.raise_for_status()
        return EmbeddingResponse.model_validate(response.json())


__all__ = [
    "EmbeddingsResource",
    "AsyncEmbeddingsResource",
    # Models
    "EmbeddingResponse",
    "EmbeddingData",
    "EmbeddingUsage",
]

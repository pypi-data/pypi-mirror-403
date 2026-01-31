"""Web Search tool using generated API client."""

from __future__ import annotations

import logging
from typing import Any, Literal, overload

from .._config import SDKConfig
from ._polling import PollingMixin, AsyncPollingMixin
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)
from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncSearchSearchAPI,
    SearchSearchAPI,
)
from .._api.generated.search.search__api__search.models import (
    SearchQueryRequest,
    URLFetchRequest,
    SearchResponse,
    Citation,
    UserLocationRequest,
    SearchRequestList,
    SearchAsyncRequestRequest,
    SearchAsyncResponse,
    SearchJobStatus,
    RankedResults,
    SearchModeResponse,
    MetricsSummary,
    QueryDecomposition,
    Entities,
)
from .._api.generated.search.enums import SearchAsyncRequestRequestMode

# Mode aliases for convenience
SearchMode = SearchAsyncRequestRequestMode


# Re-export UserLocation as alias for convenience
UserLocation = UserLocationRequest


class SearchResource(PollingMixin, BaseResource):
    """Web Search tool (sync).

    Uses generated SyncSearchSearchAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncSearchSearchAPI(self._http_client)

    @api_error_handler
    def query(
        self,
        query: str,
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        max_searches: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        user_location: UserLocation | None = None,
    ) -> SearchResponse:
        """
        Execute a web search query.

        Args:
            query: Search query
            model: Claude model to use (default: claude-3-5-haiku-20241022)
            max_tokens: Maximum tokens for response (default: 1024)
            max_searches: Maximum number of web searches (default: 5)
            allowed_domains: Only search these domains
            blocked_domains: Exclude these domains from search
            user_location: User location for localized search

        Returns:
            SearchResponse with content and citations
        """
        logger.debug("Search query: %s (max_searches=%s)", query, max_searches)
        # Build request with only non-None values
        kwargs: dict[str, Any] = {"query": query}
        if model is not None:
            kwargs["model"] = model
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if max_searches is not None:
            kwargs["max_searches"] = max_searches
        if allowed_domains is not None:
            kwargs["allowed_domains"] = allowed_domains
        if blocked_domains is not None:
            kwargs["blocked_domains"] = blocked_domains
        if user_location is not None:
            kwargs["user_location"] = user_location

        request = SearchQueryRequest(**kwargs)  # type: ignore[arg-type]
        result = self._api.query_create(request)
        logger.info("Search completed: %d citations, cost=$%.6f", len(result.citations or []), result.cost_usd or 0)
        return result

    @api_error_handler
    def fetch(
        self,
        url: str,
        *,
        prompt: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> SearchResponse:
        """
        Fetch and analyze URL content.

        Args:
            url: URL to fetch and analyze
            prompt: Prompt for analyzing the content (default: "Summarize this page")
            model: Claude model to use (default: claude-3-5-haiku-20241022)
            max_tokens: Maximum tokens for response (default: 1024)

        Returns:
            SearchResponse with analyzed content
        """
        logger.debug("Search fetch: %s", url)
        # Build request with only non-None values
        kwargs: dict[str, Any] = {"url": url}
        if prompt is not None:
            kwargs["prompt"] = prompt
        if model is not None:
            kwargs["model"] = model
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        request = URLFetchRequest(**kwargs)  # type: ignore[arg-type]
        result = self._api.fetch_create(request)
        logger.info("Search fetch completed: cost=$%.6f", result.cost_usd or 0)
        return result

    @api_error_handler
    def list(self) -> list[SearchRequestList]:
        """
        List search history.

        Returns:
            List of search request summaries (last 100 records)
        """
        return self._api.list()

    @overload
    def query_async(
        self,
        query: str,
        *,
        wait: Literal[False] = False,
        mode: str | SearchMode | None = None,
        task_prompt: str | None = None,
        model: str | None = None,
        max_results: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> SearchAsyncResponse: ...

    @overload
    def query_async(
        self,
        query: str,
        *,
        wait: Literal[True],
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        mode: str | SearchMode | None = None,
        task_prompt: str | None = None,
        model: str | None = None,
        max_results: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> RankedResults: ...

    def query_async(
        self,
        query: str,
        *,
        wait: bool = False,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        mode: str | SearchMode | None = None,
        task_prompt: str | None = None,
        model: str | None = None,
        max_results: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> SearchAsyncResponse | RankedResults:
        """
        Execute async web search with mode-based analysis depth.

        Modes (progressive capabilities):
        - search: Direct web search (fastest)
        - research: + LLM ranking + summary
        - analyze: + entity extraction
        - comprehensive: + URL fetch + deep synthesis
        - investigate: + multi-query + cross-analysis

        Args:
            query: Search query
            wait: If True, poll until completion and return results.
                  If False, return job info immediately.
            poll_interval: Seconds between status checks (only if wait=True)
            timeout: Maximum wait time in seconds (only if wait=True)
            mode: Search mode (search, research, analyze, comprehensive, investigate)
            task_prompt: Custom instructions for LLM analysis
            model: Model to use (default: openai/gpt-4o-mini)
            max_results: Maximum results to return (1-50, default: 10)
            allowed_domains: Only search these domains
            blocked_domains: Exclude these domains

        Returns:
            If wait=False: SearchAsyncResponse with job_id, request_uuid
            If wait=True: RankedResults with ranked_results, summary

        Raises:
            TimeoutError: If wait=True and job doesn't complete within timeout
            RuntimeError: If wait=True and job fails with error
        """
        logger.debug("Search async query: %s (wait=%s, mode=%s)", query, wait, mode)
        kwargs: dict[str, Any] = {"query": query}
        if mode is not None:
            kwargs["mode"] = mode.value if isinstance(mode, SearchMode) else mode
        if task_prompt is not None:
            kwargs["task_prompt"] = task_prompt
        if model is not None:
            kwargs["model"] = model
        if max_results is not None:
            kwargs["max_results"] = max_results
        if allowed_domains is not None:
            kwargs["allowed_domains"] = allowed_domains
        if blocked_domains is not None:
            kwargs["blocked_domains"] = blocked_domains

        request = SearchAsyncRequestRequest(**kwargs)  # type: ignore[arg-type]
        job = self._api.query_async_create(request)
        logger.info("Search async job queued: %s (status=%s, mode=%s)", job.request_uuid, job.status, mode)

        if not wait:
            return job

        return self._poll_until_complete(
            job_uuid=job.request_uuid,
            get_status=lambda: self.job_status(job.request_uuid),
            get_result=lambda: self.rankings(job.request_uuid),
            error_message="Search job failed",
            poll_interval=poll_interval,
            timeout=timeout,
        )

    @api_error_handler
    def results(self, uuid: str) -> SearchModeResponse:
        """
        Get full results from completed async search based on mode.

        Returns all fields populated based on the search mode:
        - search: content, citations
        - research: + ranked_results, summary, key_findings, agent_metrics
        - analyze: + entities
        - comprehensive: + synthesis, detailed_analysis
        - investigate: + sub_queries, cross_analysis, contradictions, confidence_scores

        Args:
            uuid: Request UUID from query_async()

        Returns:
            SearchModeResponse with all applicable fields

        Raises:
            APIError: If job not completed
        """
        return self._api.results_retrieve(uuid)

    @api_error_handler
    def job_status(self, uuid: str) -> SearchJobStatus:
        """
        Get status of async search job.

        Args:
            uuid: Request UUID from query_async()

        Returns:
            SearchJobStatus with status, timestamps, duration
        """
        return self._api.status_retrieve(uuid)

    @api_error_handler
    def rankings(self, uuid: str) -> RankedResults:
        """
        Get ranked results from completed async search.

        Args:
            uuid: Request UUID from query_async()

        Returns:
            RankedResults with ranked_results, summary, key_findings

        Raises:
            APIError: If job not completed
        """
        return self._api.rankings_retrieve(uuid)


class AsyncSearchResource(AsyncPollingMixin, AsyncBaseResource):
    """Web Search tool (async).

    Uses generated SearchSearchAPI client.
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SearchSearchAPI(self._http_client)

    @async_api_error_handler
    async def query(
        self,
        query: str,
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        max_searches: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        user_location: UserLocation | None = None,
    ) -> SearchResponse:
        """
        Execute a web search query.

        Args:
            query: Search query
            model: Claude model to use (default: claude-3-5-haiku-20241022)
            max_tokens: Maximum tokens for response (default: 1024)
            max_searches: Maximum number of web searches (default: 5)
            allowed_domains: Only search these domains
            blocked_domains: Exclude these domains from search
            user_location: User location for localized search

        Returns:
            SearchResponse with content and citations
        """
        logger.debug("Search async query: %s (max_searches=%s)", query, max_searches)
        # Build request with only non-None values
        kwargs: dict[str, Any] = {"query": query}
        if model is not None:
            kwargs["model"] = model
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if max_searches is not None:
            kwargs["max_searches"] = max_searches
        if allowed_domains is not None:
            kwargs["allowed_domains"] = allowed_domains
        if blocked_domains is not None:
            kwargs["blocked_domains"] = blocked_domains
        if user_location is not None:
            kwargs["user_location"] = user_location

        request = SearchQueryRequest(**kwargs)  # type: ignore[arg-type]
        result = await self._api.query_create(request)
        logger.info("Search completed: %d citations, cost=$%.6f", len(result.citations or []), result.cost_usd or 0)
        return result

    @async_api_error_handler
    async def fetch(
        self,
        url: str,
        *,
        prompt: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> SearchResponse:
        """
        Fetch and analyze URL content.

        Args:
            url: URL to fetch and analyze
            prompt: Prompt for analyzing the content (default: "Summarize this page")
            model: Claude model to use (default: claude-3-5-haiku-20241022)
            max_tokens: Maximum tokens for response (default: 1024)

        Returns:
            SearchResponse with analyzed content
        """
        logger.debug("Search async fetch: %s", url)
        # Build request with only non-None values
        kwargs: dict[str, Any] = {"url": url}
        if prompt is not None:
            kwargs["prompt"] = prompt
        if model is not None:
            kwargs["model"] = model
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        request = URLFetchRequest(**kwargs)  # type: ignore[arg-type]
        result = await self._api.fetch_create(request)
        logger.info("Search fetch completed: cost=$%.6f", result.cost_usd or 0)
        return result

    @async_api_error_handler
    async def list(self) -> list[SearchRequestList]:
        """
        List search history.

        Returns:
            List of search request summaries (last 100 records)
        """
        return await self._api.list()

    @overload
    async def query_async(
        self,
        query: str,
        *,
        wait: Literal[False] = False,
        mode: str | SearchMode | None = None,
        task_prompt: str | None = None,
        model: str | None = None,
        max_results: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> SearchAsyncResponse: ...

    @overload
    async def query_async(
        self,
        query: str,
        *,
        wait: Literal[True],
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        mode: str | SearchMode | None = None,
        task_prompt: str | None = None,
        model: str | None = None,
        max_results: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> RankedResults: ...

    async def query_async(
        self,
        query: str,
        *,
        wait: bool = False,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        mode: str | SearchMode | None = None,
        task_prompt: str | None = None,
        model: str | None = None,
        max_results: int | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
    ) -> SearchAsyncResponse | RankedResults:
        """
        Execute async web search with mode-based analysis depth.

        Modes (progressive capabilities):
        - search: Direct web search (fastest)
        - research: + LLM ranking + summary
        - analyze: + entity extraction
        - comprehensive: + URL fetch + deep synthesis
        - investigate: + multi-query + cross-analysis

        Args:
            query: Search query
            wait: If True, poll until completion and return results.
                  If False, return job info immediately.
            poll_interval: Seconds between status checks (only if wait=True)
            timeout: Maximum wait time in seconds (only if wait=True)
            mode: Search mode (search, research, analyze, comprehensive, investigate)
            task_prompt: Custom instructions for LLM analysis
            model: Model to use (default: openai/gpt-4o-mini)
            max_results: Maximum results to return (1-50, default: 10)
            allowed_domains: Only search these domains
            blocked_domains: Exclude these domains

        Returns:
            If wait=False: SearchAsyncResponse with job_id, request_uuid
            If wait=True: RankedResults with ranked_results, summary

        Raises:
            TimeoutError: If wait=True and job doesn't complete within timeout
            RuntimeError: If wait=True and job fails with error
        """
        logger.debug("Search async query: %s (wait=%s, mode=%s)", query, wait, mode)
        kwargs: dict[str, Any] = {"query": query}
        if mode is not None:
            kwargs["mode"] = mode.value if isinstance(mode, SearchMode) else mode
        if task_prompt is not None:
            kwargs["task_prompt"] = task_prompt
        if model is not None:
            kwargs["model"] = model
        if max_results is not None:
            kwargs["max_results"] = max_results
        if allowed_domains is not None:
            kwargs["allowed_domains"] = allowed_domains
        if blocked_domains is not None:
            kwargs["blocked_domains"] = blocked_domains

        request = SearchAsyncRequestRequest(**kwargs)  # type: ignore[arg-type]
        job = await self._api.query_async_create(request)
        logger.info("Search async job queued: %s (status=%s, mode=%s)", job.request_uuid, job.status, mode)

        if not wait:
            return job

        return await self._poll_until_complete(
            job_uuid=job.request_uuid,
            get_status=lambda: self.job_status(job.request_uuid),
            get_result=lambda: self.rankings(job.request_uuid),
            error_message="Search job failed",
            poll_interval=poll_interval,
            timeout=timeout,
        )

    @async_api_error_handler
    async def job_status(self, uuid: str) -> SearchJobStatus:
        """
        Get status of async search job.

        Args:
            uuid: Request UUID from query_async()

        Returns:
            SearchJobStatus with status, timestamps, duration
        """
        return await self._api.status_retrieve(uuid)

    @async_api_error_handler
    async def rankings(self, uuid: str) -> RankedResults:
        """
        Get ranked results from completed async search.

        Args:
            uuid: Request UUID from query_async()

        Returns:
            RankedResults with ranked_results, summary, key_findings

        Raises:
            APIError: If job not completed
        """
        return await self._api.rankings_retrieve(uuid)

    @async_api_error_handler
    async def results(self, uuid: str) -> SearchModeResponse:
        """
        Get full results from completed async search based on mode.

        Returns all fields populated based on the search mode:
        - search: content, citations
        - research: + ranked_results, summary, key_findings, agent_metrics
        - analyze: + entities
        - comprehensive: + synthesis, detailed_analysis
        - investigate: + sub_queries, cross_analysis, contradictions, confidence_scores

        Args:
            uuid: Request UUID from query_async()

        Returns:
            SearchModeResponse with all applicable fields

        Raises:
            APIError: If job not completed
        """
        return await self._api.results_retrieve(uuid)


__all__ = [
    "SearchResource",
    "AsyncSearchResource",
    # Mode enum
    "SearchMode",
    # Models
    "SearchResponse",
    "Citation",
    "UserLocation",
    "SearchRequestList",
    "SearchQueryRequest",
    "URLFetchRequest",
    "UserLocationRequest",
    # Async job models
    "SearchAsyncRequestRequest",
    "SearchAsyncResponse",
    "SearchJobStatus",
    "RankedResults",
    # Full results model
    "SearchModeResponse",
    "MetricsSummary",
    "QueryDecomposition",
    "Entities",
]

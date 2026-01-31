# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union

import httpx

from ..types import search_repo_search_params, search_repo_natural_language_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.search_repo_search_response import SearchRepoSearchResponse
from ..types.search_repo_natural_language_response import SearchRepoNaturalLanguageResponse

__all__ = ["SearchReposResource", "AsyncSearchReposResource"]


class SearchReposResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SearchReposResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return SearchReposResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SearchReposResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return SearchReposResourceWithStreamingResponse(self)

    def natural_language(
        self,
        *,
        query: str,
        after: str | Omit = omit,
        apply_filters_to_include_attributes: bool | Omit = omit,
        enable_pagination: bool | Omit = omit,
        filter_user_include_attributes: bool | Omit = omit,
        first: int | Omit = omit,
        include_attributes: search_repo_natural_language_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        rank_by: search_repo_natural_language_params.RankBy | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoNaturalLanguageResponse:
        """
        Natural language search that uses AI to understand your query and automatically
        generate search terms and filters. Requires SEARCH service. Credits: 1 per
        result returned + 1 for AI processing + graph relationship credits if
        includeAttributes is specified.

        Args:
          query: Natural language query describing the repositories you want to find

          after: Cursor for pagination (from previous response pageInfo.endCursor)

          apply_filters_to_include_attributes: When true, applies the LLM-generated filter to all user-returning
              includeAttributes (contributors, starrers). Alias for
              filterUserIncludeAttributes.

          enable_pagination: Enable cursor-based pagination to fetch results across multiple requests

          filter_user_include_attributes: [Deprecated: Use applyFiltersToIncludeAttributes] When true, applies the
              LLM-generated filter to all user-returning includeAttributes (contributors,
              starrers).

          first: Alias for maxResults (takes precedence if both provided)

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          rank_by: Custom ranking formula (AST expression). If not provided, uses default
              log-normalized 70/20/10 formula (70% semantic similarity, 20% popularity, 10%
              activity).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/search/repos/natural-language",
            body=maybe_transform(
                {
                    "query": query,
                    "after": after,
                    "apply_filters_to_include_attributes": apply_filters_to_include_attributes,
                    "enable_pagination": enable_pagination,
                    "filter_user_include_attributes": filter_user_include_attributes,
                    "first": first,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                    "rank_by": rank_by,
                },
                search_repo_natural_language_params.SearchRepoNaturalLanguageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoNaturalLanguageResponse,
        )

    def search(
        self,
        *,
        query: Union[str, SequenceNotStr[str], None],
        after: str | Omit = omit,
        apply_filters_to_include_attributes: bool | Omit = omit,
        enable_pagination: bool | Omit = omit,
        filters: search_repo_search_params.Filters | Omit = omit,
        first: int | Omit = omit,
        include_attributes: search_repo_search_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        rank_by: search_repo_search_params.RankBy | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoSearchResponse:
        """
        Semantic search across repository READMEs and descriptions using vector
        embeddings and cosine similarity. Results include relevance scores. Requires
        SEARCH service. Credits: 1 per result returned.

        Args:
          query: Search query for semantic search across repository README and description using
              vector embeddings. Supports: string (single query), string[] (RRF fusion), null
              (filter-only)

          after: Cursor for pagination (from previous response pageInfo.endCursor)

          apply_filters_to_include_attributes: When true, applies the search filter to all user-returning includeAttributes
              (contributors, starrers). This filters the returned users to match the same
              criteria.

          enable_pagination: Enable cursor-based pagination to fetch results across multiple requests

          filters: Filters to apply (required)

          first: Alias for maxResults (takes precedence if both provided)

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          rank_by: Custom ranking formula (AST expression). If not provided, uses default
              log-normalized 70/20/10 formula (70% semantic similarity, 20% popularity, 10%
              activity).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/search/repos",
            body=maybe_transform(
                {
                    "query": query,
                    "after": after,
                    "apply_filters_to_include_attributes": apply_filters_to_include_attributes,
                    "enable_pagination": enable_pagination,
                    "filters": filters,
                    "first": first,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                    "rank_by": rank_by,
                },
                search_repo_search_params.SearchRepoSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoSearchResponse,
        )


class AsyncSearchReposResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSearchReposResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncSearchReposResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSearchReposResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/bountylaboratories/python-sdk#with_streaming_response
        """
        return AsyncSearchReposResourceWithStreamingResponse(self)

    async def natural_language(
        self,
        *,
        query: str,
        after: str | Omit = omit,
        apply_filters_to_include_attributes: bool | Omit = omit,
        enable_pagination: bool | Omit = omit,
        filter_user_include_attributes: bool | Omit = omit,
        first: int | Omit = omit,
        include_attributes: search_repo_natural_language_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        rank_by: search_repo_natural_language_params.RankBy | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoNaturalLanguageResponse:
        """
        Natural language search that uses AI to understand your query and automatically
        generate search terms and filters. Requires SEARCH service. Credits: 1 per
        result returned + 1 for AI processing + graph relationship credits if
        includeAttributes is specified.

        Args:
          query: Natural language query describing the repositories you want to find

          after: Cursor for pagination (from previous response pageInfo.endCursor)

          apply_filters_to_include_attributes: When true, applies the LLM-generated filter to all user-returning
              includeAttributes (contributors, starrers). Alias for
              filterUserIncludeAttributes.

          enable_pagination: Enable cursor-based pagination to fetch results across multiple requests

          filter_user_include_attributes: [Deprecated: Use applyFiltersToIncludeAttributes] When true, applies the
              LLM-generated filter to all user-returning includeAttributes (contributors,
              starrers).

          first: Alias for maxResults (takes precedence if both provided)

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          rank_by: Custom ranking formula (AST expression). If not provided, uses default
              log-normalized 70/20/10 formula (70% semantic similarity, 20% popularity, 10%
              activity).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/search/repos/natural-language",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "after": after,
                    "apply_filters_to_include_attributes": apply_filters_to_include_attributes,
                    "enable_pagination": enable_pagination,
                    "filter_user_include_attributes": filter_user_include_attributes,
                    "first": first,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                    "rank_by": rank_by,
                },
                search_repo_natural_language_params.SearchRepoNaturalLanguageParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoNaturalLanguageResponse,
        )

    async def search(
        self,
        *,
        query: Union[str, SequenceNotStr[str], None],
        after: str | Omit = omit,
        apply_filters_to_include_attributes: bool | Omit = omit,
        enable_pagination: bool | Omit = omit,
        filters: search_repo_search_params.Filters | Omit = omit,
        first: int | Omit = omit,
        include_attributes: search_repo_search_params.IncludeAttributes | Omit = omit,
        max_results: int | Omit = omit,
        rank_by: search_repo_search_params.RankBy | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SearchRepoSearchResponse:
        """
        Semantic search across repository READMEs and descriptions using vector
        embeddings and cosine similarity. Results include relevance scores. Requires
        SEARCH service. Credits: 1 per result returned.

        Args:
          query: Search query for semantic search across repository README and description using
              vector embeddings. Supports: string (single query), string[] (RRF fusion), null
              (filter-only)

          after: Cursor for pagination (from previous response pageInfo.endCursor)

          apply_filters_to_include_attributes: When true, applies the search filter to all user-returning includeAttributes
              (contributors, starrers). This filters the returned users to match the same
              criteria.

          enable_pagination: Enable cursor-based pagination to fetch results across multiple requests

          filters: Filters to apply (required)

          first: Alias for maxResults (takes precedence if both provided)

          include_attributes: Optional graph relationships to include (owner, contributors, starrers)

          max_results: Maximum number of results to return (default: 100, max: 1000)

          rank_by: Custom ranking formula (AST expression). If not provided, uses default
              log-normalized 70/20/10 formula (70% semantic similarity, 20% popularity, 10%
              activity).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/search/repos",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "after": after,
                    "apply_filters_to_include_attributes": apply_filters_to_include_attributes,
                    "enable_pagination": enable_pagination,
                    "filters": filters,
                    "first": first,
                    "include_attributes": include_attributes,
                    "max_results": max_results,
                    "rank_by": rank_by,
                },
                search_repo_search_params.SearchRepoSearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SearchRepoSearchResponse,
        )


class SearchReposResourceWithRawResponse:
    def __init__(self, search_repos: SearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = to_raw_response_wrapper(
            search_repos.natural_language,
        )
        self.search = to_raw_response_wrapper(
            search_repos.search,
        )


class AsyncSearchReposResourceWithRawResponse:
    def __init__(self, search_repos: AsyncSearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = async_to_raw_response_wrapper(
            search_repos.natural_language,
        )
        self.search = async_to_raw_response_wrapper(
            search_repos.search,
        )


class SearchReposResourceWithStreamingResponse:
    def __init__(self, search_repos: SearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = to_streamed_response_wrapper(
            search_repos.natural_language,
        )
        self.search = to_streamed_response_wrapper(
            search_repos.search,
        )


class AsyncSearchReposResourceWithStreamingResponse:
    def __init__(self, search_repos: AsyncSearchReposResource) -> None:
        self._search_repos = search_repos

        self.natural_language = async_to_streamed_response_wrapper(
            search_repos.natural_language,
        )
        self.search = async_to_streamed_response_wrapper(
            search_repos.search,
        )

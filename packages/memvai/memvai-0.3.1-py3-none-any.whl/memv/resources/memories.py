# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ..types import memory_add_params, memory_search_params
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
from ..types.memory_add_response import MemoryAddResponse
from ..types.memory_search_response import MemorySearchResponse

__all__ = ["MemoriesResource", "AsyncMemoriesResource"]


class MemoriesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MemoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/mem-v/memv-python#accessing-raw-response-data-eg-headers
        """
        return MemoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MemoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/mem-v/memv-python#with_streaming_response
        """
        return MemoriesResourceWithStreamingResponse(self)

    def add(
        self,
        *,
        memories: Iterable[memory_add_params.Memory],
        space_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryAddResponse:
        """
        Add one or more memories to a space's knowledge graph.

        **Required scope:** `spaces:write`

        Args:
          space_id: The memory space to add memories to

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/memories",
            body=maybe_transform(
                {
                    "memories": memories,
                    "space_id": space_id,
                },
                memory_add_params.MemoryAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryAddResponse,
        )

    def search(
        self,
        *,
        query: str,
        space_ids: SequenceNotStr[str],
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemorySearchResponse:
        """Search for relevant memories using natural language.

        Returns top-k semantic
        matches from the knowledge graph.

        **Required scope:** `spaces:read`

        Args:
          query: Natural language query to search for

          space_ids: Memory spaces to search within

          max_results: Maximum number of results to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/memories/search",
            body=maybe_transform(
                {
                    "query": query,
                    "space_ids": space_ids,
                    "max_results": max_results,
                },
                memory_search_params.MemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemorySearchResponse,
        )


class AsyncMemoriesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMemoriesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/mem-v/memv-python#accessing-raw-response-data-eg-headers
        """
        return AsyncMemoriesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMemoriesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/mem-v/memv-python#with_streaming_response
        """
        return AsyncMemoriesResourceWithStreamingResponse(self)

    async def add(
        self,
        *,
        memories: Iterable[memory_add_params.Memory],
        space_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemoryAddResponse:
        """
        Add one or more memories to a space's knowledge graph.

        **Required scope:** `spaces:write`

        Args:
          space_id: The memory space to add memories to

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/memories",
            body=await async_maybe_transform(
                {
                    "memories": memories,
                    "space_id": space_id,
                },
                memory_add_params.MemoryAddParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryAddResponse,
        )

    async def search(
        self,
        *,
        query: str,
        space_ids: SequenceNotStr[str],
        max_results: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MemorySearchResponse:
        """Search for relevant memories using natural language.

        Returns top-k semantic
        matches from the knowledge graph.

        **Required scope:** `spaces:read`

        Args:
          query: Natural language query to search for

          space_ids: Memory spaces to search within

          max_results: Maximum number of results to return

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/memories/search",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "space_ids": space_ids,
                    "max_results": max_results,
                },
                memory_search_params.MemorySearchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemorySearchResponse,
        )


class MemoriesResourceWithRawResponse:
    def __init__(self, memories: MemoriesResource) -> None:
        self._memories = memories

        self.add = to_raw_response_wrapper(
            memories.add,
        )
        self.search = to_raw_response_wrapper(
            memories.search,
        )


class AsyncMemoriesResourceWithRawResponse:
    def __init__(self, memories: AsyncMemoriesResource) -> None:
        self._memories = memories

        self.add = async_to_raw_response_wrapper(
            memories.add,
        )
        self.search = async_to_raw_response_wrapper(
            memories.search,
        )


class MemoriesResourceWithStreamingResponse:
    def __init__(self, memories: MemoriesResource) -> None:
        self._memories = memories

        self.add = to_streamed_response_wrapper(
            memories.add,
        )
        self.search = to_streamed_response_wrapper(
            memories.search,
        )


class AsyncMemoriesResourceWithStreamingResponse:
    def __init__(self, memories: AsyncMemoriesResource) -> None:
        self._memories = memories

        self.add = async_to_streamed_response_wrapper(
            memories.add,
        )
        self.search = async_to_streamed_response_wrapper(
            memories.search,
        )

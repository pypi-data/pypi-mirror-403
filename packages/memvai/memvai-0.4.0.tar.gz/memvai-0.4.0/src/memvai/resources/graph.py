# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from .._types import Body, Query, Headers, NotGiven, not_given
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["GraphResource", "AsyncGraphResource"]


class GraphResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> GraphResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/mem-v/memv-python#accessing-raw-response-data-eg-headers
        """
        return GraphResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GraphResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/mem-v/memv-python#with_streaming_response
        """
        return GraphResourceWithStreamingResponse(self)

    def retrieve_triplets(
        self,
        id: str,
        *,
        type: Literal["user", "group"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Access the underlying knowledge graph of entities and relationships extracted
        from memories

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/graph/{type}/{id}/triplets",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncGraphResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncGraphResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/mem-v/memv-python#accessing-raw-response-data-eg-headers
        """
        return AsyncGraphResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGraphResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/mem-v/memv-python#with_streaming_response
        """
        return AsyncGraphResourceWithStreamingResponse(self)

    async def retrieve_triplets(
        self,
        id: str,
        *,
        type: Literal["user", "group"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Access the underlying knowledge graph of entities and relationships extracted
        from memories

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/graph/{type}/{id}/triplets",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class GraphResourceWithRawResponse:
    def __init__(self, graph: GraphResource) -> None:
        self._graph = graph

        self.retrieve_triplets = to_raw_response_wrapper(
            graph.retrieve_triplets,
        )


class AsyncGraphResourceWithRawResponse:
    def __init__(self, graph: AsyncGraphResource) -> None:
        self._graph = graph

        self.retrieve_triplets = async_to_raw_response_wrapper(
            graph.retrieve_triplets,
        )


class GraphResourceWithStreamingResponse:
    def __init__(self, graph: GraphResource) -> None:
        self._graph = graph

        self.retrieve_triplets = to_streamed_response_wrapper(
            graph.retrieve_triplets,
        )


class AsyncGraphResourceWithStreamingResponse:
    def __init__(self, graph: AsyncGraphResource) -> None:
        self._graph = graph

        self.retrieve_triplets = async_to_streamed_response_wrapper(
            graph.retrieve_triplets,
        )

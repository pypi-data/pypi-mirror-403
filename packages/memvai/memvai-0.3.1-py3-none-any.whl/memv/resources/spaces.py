# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import space_create_params, space_delete_params, space_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.space_list_response import SpaceListResponse
from ..types.space_create_response import SpaceCreateResponse
from ..types.space_delete_response import SpaceDeleteResponse
from ..types.space_update_response import SpaceUpdateResponse
from ..types.space_retrieve_response import SpaceRetrieveResponse
from ..types.space_get_stats_response import SpaceGetStatsResponse

__all__ = ["SpacesResource", "AsyncSpacesResource"]


class SpacesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SpacesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/mem-v/memv-python#accessing-raw-response-data-eg-headers
        """
        return SpacesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SpacesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/mem-v/memv-python#with_streaming_response
        """
        return SpacesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        description: Optional[str] | Omit = omit,
        is_public: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceCreateResponse:
        """
        Create a new memory space to store and organize memories for an agent or context

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/spaces",
            body=maybe_transform(
                {
                    "name": name,
                    "description": description,
                    "is_public": is_public,
                },
                space_create_params.SpaceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceCreateResponse,
        )

    def retrieve(
        self,
        space_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceRetrieveResponse:
        """
        Get a space

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not space_id:
            raise ValueError(f"Expected a non-empty value for `space_id` but received {space_id!r}")
        return self._get(
            f"/spaces/{space_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceRetrieveResponse,
        )

    def update(
        self,
        *,
        space_id: str,
        description: Optional[str] | Omit = omit,
        is_public: bool | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceUpdateResponse:
        """
        Update a memory space

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._patch(
            "/spaces",
            body=maybe_transform(
                {
                    "space_id": space_id,
                    "description": description,
                    "is_public": is_public,
                    "name": name,
                },
                space_update_params.SpaceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceUpdateResponse,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceListResponse:
        """Get all memory spaces for the authenticated user.

        Each space is an isolated
        memory context.
        """
        return self._get(
            "/spaces",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceListResponse,
        )

    def delete(
        self,
        *,
        space_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceDeleteResponse:
        """
        Delete a memory space

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._delete(
            "/spaces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"space_id": space_id}, space_delete_params.SpaceDeleteParams),
            ),
            cast_to=SpaceDeleteResponse,
        )

    def get_stats(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceGetStatsResponse:
        """Get memory spaces with content counts"""
        return self._get(
            "/spaces/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceGetStatsResponse,
        )


class AsyncSpacesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSpacesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/mem-v/memv-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSpacesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSpacesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/mem-v/memv-python#with_streaming_response
        """
        return AsyncSpacesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        description: Optional[str] | Omit = omit,
        is_public: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceCreateResponse:
        """
        Create a new memory space to store and organize memories for an agent or context

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/spaces",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "description": description,
                    "is_public": is_public,
                },
                space_create_params.SpaceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceCreateResponse,
        )

    async def retrieve(
        self,
        space_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceRetrieveResponse:
        """
        Get a space

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not space_id:
            raise ValueError(f"Expected a non-empty value for `space_id` but received {space_id!r}")
        return await self._get(
            f"/spaces/{space_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceRetrieveResponse,
        )

    async def update(
        self,
        *,
        space_id: str,
        description: Optional[str] | Omit = omit,
        is_public: bool | Omit = omit,
        name: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceUpdateResponse:
        """
        Update a memory space

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._patch(
            "/spaces",
            body=await async_maybe_transform(
                {
                    "space_id": space_id,
                    "description": description,
                    "is_public": is_public,
                    "name": name,
                },
                space_update_params.SpaceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceUpdateResponse,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceListResponse:
        """Get all memory spaces for the authenticated user.

        Each space is an isolated
        memory context.
        """
        return await self._get(
            "/spaces",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceListResponse,
        )

    async def delete(
        self,
        *,
        space_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceDeleteResponse:
        """
        Delete a memory space

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._delete(
            "/spaces",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"space_id": space_id}, space_delete_params.SpaceDeleteParams),
            ),
            cast_to=SpaceDeleteResponse,
        )

    async def get_stats(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SpaceGetStatsResponse:
        """Get memory spaces with content counts"""
        return await self._get(
            "/spaces/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SpaceGetStatsResponse,
        )


class SpacesResourceWithRawResponse:
    def __init__(self, spaces: SpacesResource) -> None:
        self._spaces = spaces

        self.create = to_raw_response_wrapper(
            spaces.create,
        )
        self.retrieve = to_raw_response_wrapper(
            spaces.retrieve,
        )
        self.update = to_raw_response_wrapper(
            spaces.update,
        )
        self.list = to_raw_response_wrapper(
            spaces.list,
        )
        self.delete = to_raw_response_wrapper(
            spaces.delete,
        )
        self.get_stats = to_raw_response_wrapper(
            spaces.get_stats,
        )


class AsyncSpacesResourceWithRawResponse:
    def __init__(self, spaces: AsyncSpacesResource) -> None:
        self._spaces = spaces

        self.create = async_to_raw_response_wrapper(
            spaces.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            spaces.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            spaces.update,
        )
        self.list = async_to_raw_response_wrapper(
            spaces.list,
        )
        self.delete = async_to_raw_response_wrapper(
            spaces.delete,
        )
        self.get_stats = async_to_raw_response_wrapper(
            spaces.get_stats,
        )


class SpacesResourceWithStreamingResponse:
    def __init__(self, spaces: SpacesResource) -> None:
        self._spaces = spaces

        self.create = to_streamed_response_wrapper(
            spaces.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            spaces.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            spaces.update,
        )
        self.list = to_streamed_response_wrapper(
            spaces.list,
        )
        self.delete = to_streamed_response_wrapper(
            spaces.delete,
        )
        self.get_stats = to_streamed_response_wrapper(
            spaces.get_stats,
        )


class AsyncSpacesResourceWithStreamingResponse:
    def __init__(self, spaces: AsyncSpacesResource) -> None:
        self._spaces = spaces

        self.create = async_to_streamed_response_wrapper(
            spaces.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            spaces.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            spaces.update,
        )
        self.list = async_to_streamed_response_wrapper(
            spaces.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            spaces.delete,
        )
        self.get_stats = async_to_streamed_response_wrapper(
            spaces.get_stats,
        )

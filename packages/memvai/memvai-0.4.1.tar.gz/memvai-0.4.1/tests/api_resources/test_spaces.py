# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from memvai import Memv, AsyncMemv
from tests.utils import assert_matches_type
from memvai.types import (
    SpaceListResponse,
    SpaceCreateResponse,
    SpaceDeleteResponse,
    SpaceUpdateResponse,
    SpaceGetStatsResponse,
    SpaceRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSpaces:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Memv) -> None:
        space = client.spaces.create(
            name="name",
        )
        assert_matches_type(SpaceCreateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Memv) -> None:
        space = client.spaces.create(
            name="name",
            description="description",
            is_public=True,
        )
        assert_matches_type(SpaceCreateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Memv) -> None:
        response = client.spaces.with_raw_response.create(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = response.parse()
        assert_matches_type(SpaceCreateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Memv) -> None:
        with client.spaces.with_streaming_response.create(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = response.parse()
            assert_matches_type(SpaceCreateResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Memv) -> None:
        space = client.spaces.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SpaceRetrieveResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Memv) -> None:
        response = client.spaces.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = response.parse()
        assert_matches_type(SpaceRetrieveResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Memv) -> None:
        with client.spaces.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = response.parse()
            assert_matches_type(SpaceRetrieveResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `space_id` but received ''"):
            client.spaces.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Memv) -> None:
        space = client.spaces.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SpaceUpdateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Memv) -> None:
        space = client.spaces.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            description="description",
            is_public=True,
            name="name",
        )
        assert_matches_type(SpaceUpdateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Memv) -> None:
        response = client.spaces.with_raw_response.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = response.parse()
        assert_matches_type(SpaceUpdateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Memv) -> None:
        with client.spaces.with_streaming_response.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = response.parse()
            assert_matches_type(SpaceUpdateResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Memv) -> None:
        space = client.spaces.list()
        assert_matches_type(SpaceListResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Memv) -> None:
        response = client.spaces.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = response.parse()
        assert_matches_type(SpaceListResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Memv) -> None:
        with client.spaces.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = response.parse()
            assert_matches_type(SpaceListResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Memv) -> None:
        space = client.spaces.delete(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SpaceDeleteResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Memv) -> None:
        response = client.spaces.with_raw_response.delete(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = response.parse()
        assert_matches_type(SpaceDeleteResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Memv) -> None:
        with client.spaces.with_streaming_response.delete(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = response.parse()
            assert_matches_type(SpaceDeleteResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_stats(self, client: Memv) -> None:
        space = client.spaces.get_stats()
        assert_matches_type(SpaceGetStatsResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_stats(self, client: Memv) -> None:
        response = client.spaces.with_raw_response.get_stats()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = response.parse()
        assert_matches_type(SpaceGetStatsResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_stats(self, client: Memv) -> None:
        with client.spaces.with_streaming_response.get_stats() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = response.parse()
            assert_matches_type(SpaceGetStatsResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSpaces:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.create(
            name="name",
        )
        assert_matches_type(SpaceCreateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.create(
            name="name",
            description="description",
            is_public=True,
        )
        assert_matches_type(SpaceCreateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncMemv) -> None:
        response = await async_client.spaces.with_raw_response.create(
            name="name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = await response.parse()
        assert_matches_type(SpaceCreateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncMemv) -> None:
        async with async_client.spaces.with_streaming_response.create(
            name="name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = await response.parse()
            assert_matches_type(SpaceCreateResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SpaceRetrieveResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncMemv) -> None:
        response = await async_client.spaces.with_raw_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = await response.parse()
        assert_matches_type(SpaceRetrieveResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncMemv) -> None:
        async with async_client.spaces.with_streaming_response.retrieve(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = await response.parse()
            assert_matches_type(SpaceRetrieveResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `space_id` but received ''"):
            await async_client.spaces.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SpaceUpdateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            description="description",
            is_public=True,
            name="name",
        )
        assert_matches_type(SpaceUpdateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncMemv) -> None:
        response = await async_client.spaces.with_raw_response.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = await response.parse()
        assert_matches_type(SpaceUpdateResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncMemv) -> None:
        async with async_client.spaces.with_streaming_response.update(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = await response.parse()
            assert_matches_type(SpaceUpdateResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.list()
        assert_matches_type(SpaceListResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncMemv) -> None:
        response = await async_client.spaces.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = await response.parse()
        assert_matches_type(SpaceListResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncMemv) -> None:
        async with async_client.spaces.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = await response.parse()
            assert_matches_type(SpaceListResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.delete(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(SpaceDeleteResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncMemv) -> None:
        response = await async_client.spaces.with_raw_response.delete(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = await response.parse()
        assert_matches_type(SpaceDeleteResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncMemv) -> None:
        async with async_client.spaces.with_streaming_response.delete(
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = await response.parse()
            assert_matches_type(SpaceDeleteResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_stats(self, async_client: AsyncMemv) -> None:
        space = await async_client.spaces.get_stats()
        assert_matches_type(SpaceGetStatsResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_stats(self, async_client: AsyncMemv) -> None:
        response = await async_client.spaces.with_raw_response.get_stats()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        space = await response.parse()
        assert_matches_type(SpaceGetStatsResponse, space, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_stats(self, async_client: AsyncMemv) -> None:
        async with async_client.spaces.with_streaming_response.get_stats() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            space = await response.parse()
            assert_matches_type(SpaceGetStatsResponse, space, path=["response"])

        assert cast(Any, response.is_closed) is True

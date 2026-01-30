# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from memv import Memv, AsyncMemv
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGraph:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_triplets(self, client: Memv) -> None:
        graph = client.graph.retrieve_triplets(
            id="id",
            type="user",
        )
        assert_matches_type(object, graph, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_triplets(self, client: Memv) -> None:
        response = client.graph.with_raw_response.retrieve_triplets(
            id="id",
            type="user",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        graph = response.parse()
        assert_matches_type(object, graph, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_triplets(self, client: Memv) -> None:
        with client.graph.with_streaming_response.retrieve_triplets(
            id="id",
            type="user",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            graph = response.parse()
            assert_matches_type(object, graph, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_triplets(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.graph.with_raw_response.retrieve_triplets(
                id="",
                type="user",
            )


class TestAsyncGraph:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_triplets(self, async_client: AsyncMemv) -> None:
        graph = await async_client.graph.retrieve_triplets(
            id="id",
            type="user",
        )
        assert_matches_type(object, graph, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_triplets(self, async_client: AsyncMemv) -> None:
        response = await async_client.graph.with_raw_response.retrieve_triplets(
            id="id",
            type="user",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        graph = await response.parse()
        assert_matches_type(object, graph, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_triplets(self, async_client: AsyncMemv) -> None:
        async with async_client.graph.with_streaming_response.retrieve_triplets(
            id="id",
            type="user",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            graph = await response.parse()
            assert_matches_type(object, graph, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_triplets(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.graph.with_raw_response.retrieve_triplets(
                id="",
                type="user",
            )

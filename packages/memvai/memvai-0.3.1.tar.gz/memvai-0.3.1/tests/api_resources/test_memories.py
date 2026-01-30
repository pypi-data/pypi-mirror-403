# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from memv import Memv, AsyncMemv
from memv.types import MemoryAddResponse, MemorySearchResponse
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMemories:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add(self, client: Memv) -> None:
        memory = client.memories.add(
            memories=[{"content": "content"}],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add(self, client: Memv) -> None:
        response = client.memories.with_raw_response.add(
            memories=[{"content": "content"}],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add(self, client: Memv) -> None:
        with client.memories.with_streaming_response.add(
            memories=[{"content": "content"}],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryAddResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: Memv) -> None:
        memory = client.memories.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search_with_all_params(self, client: Memv) -> None:
        memory = client.memories.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
            max_results=50,
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: Memv) -> None:
        response = client.memories.with_raw_response.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: Memv) -> None:
        with client.memories.with_streaming_response.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMemories:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add(self, async_client: AsyncMemv) -> None:
        memory = await async_client.memories.add(
            memories=[{"content": "content"}],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncMemv) -> None:
        response = await async_client.memories.with_raw_response.add(
            memories=[{"content": "content"}],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryAddResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncMemv) -> None:
        async with async_client.memories.with_streaming_response.add(
            memories=[{"content": "content"}],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryAddResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncMemv) -> None:
        memory = await async_client.memories.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncMemv) -> None:
        memory = await async_client.memories.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
            max_results=50,
        )
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncMemv) -> None:
        response = await async_client.memories.with_raw_response.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncMemv) -> None:
        async with async_client.memories.with_streaming_response.search(
            query="query",
            space_ids=["182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

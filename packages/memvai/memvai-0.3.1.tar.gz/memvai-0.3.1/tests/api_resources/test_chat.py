# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from memv import Memv, AsyncMemv
from memv.types import ChatQueryMemoriesResponse
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestChat:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query_memories(self, client: Memv) -> None:
        chat = client.chat.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )
        assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_query_memories_with_all_params(self, client: Memv) -> None:
        chat = client.chat.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
            add_memory_mode=True,
        )
        assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_query_memories(self, client: Memv) -> None:
        response = client.chat.with_raw_response.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = response.parse()
        assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_query_memories(self, client: Memv) -> None:
        with client.chat.with_streaming_response.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = response.parse()
            assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncChat:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query_memories(self, async_client: AsyncMemv) -> None:
        chat = await async_client.chat.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )
        assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_query_memories_with_all_params(self, async_client: AsyncMemv) -> None:
        chat = await async_client.chat.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
            add_memory_mode=True,
        )
        assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_query_memories(self, async_client: AsyncMemv) -> None:
        response = await async_client.chat.with_raw_response.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chat = await response.parse()
        assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_query_memories(self, async_client: AsyncMemv) -> None:
        async with async_client.chat.with_streaming_response.query_memories(
            group_id="groupId",
            messages=[
                {
                    "content": "content",
                    "role": "user",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chat = await response.parse()
            assert_matches_type(ChatQueryMemoriesResponse, chat, path=["response"])

        assert cast(Any, response.is_closed) is True

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from memv import Memv, AsyncMemv
from memv.types import (
    VideoListResponse,
    VideoDeleteResponse,
    VideoDownloadResponse,
)
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVideos:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Memv) -> None:
        video = client.videos.list()
        assert_matches_type(VideoListResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Memv) -> None:
        video = client.videos.list(
            limit=100,
            offset=0,
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            status="processing",
        )
        assert_matches_type(VideoListResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Memv) -> None:
        response = client.videos.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        video = response.parse()
        assert_matches_type(VideoListResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Memv) -> None:
        with client.videos.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            video = response.parse()
            assert_matches_type(VideoListResponse, video, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Memv) -> None:
        video = client.videos.delete(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(VideoDeleteResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Memv) -> None:
        response = client.videos.with_raw_response.delete(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        video = response.parse()
        assert_matches_type(VideoDeleteResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Memv) -> None:
        with client.videos.with_streaming_response.delete(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            video = response.parse()
            assert_matches_type(VideoDeleteResponse, video, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download(self, client: Memv) -> None:
        video = client.videos.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(VideoDownloadResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_download_with_all_params(self, client: Memv) -> None:
        video = client.videos.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            return_url=True,
            type="download",
        )
        assert_matches_type(VideoDownloadResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_download(self, client: Memv) -> None:
        response = client.videos.with_raw_response.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        video = response.parse()
        assert_matches_type(VideoDownloadResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_download(self, client: Memv) -> None:
        with client.videos.with_streaming_response.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            video = response.parse()
            assert_matches_type(VideoDownloadResponse, video, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_download(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `video_id` but received ''"):
            client.videos.with_raw_response.download(
                video_id="",
            )


class TestAsyncVideos:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncMemv) -> None:
        video = await async_client.videos.list()
        assert_matches_type(VideoListResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncMemv) -> None:
        video = await async_client.videos.list(
            limit=100,
            offset=0,
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            status="processing",
        )
        assert_matches_type(VideoListResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncMemv) -> None:
        response = await async_client.videos.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        video = await response.parse()
        assert_matches_type(VideoListResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncMemv) -> None:
        async with async_client.videos.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            video = await response.parse()
            assert_matches_type(VideoListResponse, video, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncMemv) -> None:
        video = await async_client.videos.delete(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(VideoDeleteResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncMemv) -> None:
        response = await async_client.videos.with_raw_response.delete(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        video = await response.parse()
        assert_matches_type(VideoDeleteResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncMemv) -> None:
        async with async_client.videos.with_streaming_response.delete(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            video = await response.parse()
            assert_matches_type(VideoDeleteResponse, video, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download(self, async_client: AsyncMemv) -> None:
        video = await async_client.videos.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(VideoDownloadResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_download_with_all_params(self, async_client: AsyncMemv) -> None:
        video = await async_client.videos.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            return_url=True,
            type="download",
        )
        assert_matches_type(VideoDownloadResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_download(self, async_client: AsyncMemv) -> None:
        response = await async_client.videos.with_raw_response.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        video = await response.parse()
        assert_matches_type(VideoDownloadResponse, video, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_download(self, async_client: AsyncMemv) -> None:
        async with async_client.videos.with_streaming_response.download(
            video_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            video = await response.parse()
            assert_matches_type(VideoDownloadResponse, video, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_download(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `video_id` but received ''"):
            await async_client.videos.with_raw_response.download(
                video_id="",
            )

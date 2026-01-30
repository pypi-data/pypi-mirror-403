# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from memv import Memv, AsyncMemv
from tests.utils import assert_matches_type
from memv.types.upload import (
    BatchCancelResponse,
    BatchCreateResponse,
    BatchGetStatusResponse,
    BatchMarkFileUploadedResponse,
    BatchProcessUploadedMemoriesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBatch:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Memv) -> None:
        batch = client.upload.batch.create(
            files=[
                {
                    "file_name": "fileName",
                    "file_type": "fileType",
                }
            ],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchCreateResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Memv) -> None:
        response = client.upload.batch.with_raw_response.create(
            files=[
                {
                    "file_name": "fileName",
                    "file_type": "fileType",
                }
            ],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(BatchCreateResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Memv) -> None:
        with client.upload.batch.with_streaming_response.create(
            files=[
                {
                    "file_name": "fileName",
                    "file_type": "fileType",
                }
            ],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(BatchCreateResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: Memv) -> None:
        batch = client.upload.batch.cancel(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchCancelResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: Memv) -> None:
        response = client.upload.batch.with_raw_response.cancel(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(BatchCancelResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: Memv) -> None:
        with client.upload.batch.with_streaming_response.cancel(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(BatchCancelResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.upload.batch.with_raw_response.cancel(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_status(self, client: Memv) -> None:
        batch = client.upload.batch.get_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchGetStatusResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_status(self, client: Memv) -> None:
        response = client.upload.batch.with_raw_response.get_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(BatchGetStatusResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_status(self, client: Memv) -> None:
        with client.upload.batch.with_streaming_response.get_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(BatchGetStatusResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_status(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.upload.batch.with_raw_response.get_status(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_mark_file_uploaded(self, client: Memv) -> None:
        batch = client.upload.batch.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
        )
        assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_mark_file_uploaded_with_all_params(self, client: Memv) -> None:
        batch = client.upload.batch.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
            r2_key="r2Key",
        )
        assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_mark_file_uploaded(self, client: Memv) -> None:
        response = client.upload.batch.with_raw_response.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_mark_file_uploaded(self, client: Memv) -> None:
        with client.upload.batch.with_streaming_response.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_mark_file_uploaded(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.upload.batch.with_raw_response.mark_file_uploaded(
                batch_id="",
                index=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_process_uploaded_memories(self, client: Memv) -> None:
        batch = client.upload.batch.process_uploaded_memories(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchProcessUploadedMemoriesResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_process_uploaded_memories(self, client: Memv) -> None:
        response = client.upload.batch.with_raw_response.process_uploaded_memories(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = response.parse()
        assert_matches_type(BatchProcessUploadedMemoriesResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_process_uploaded_memories(self, client: Memv) -> None:
        with client.upload.batch.with_streaming_response.process_uploaded_memories(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = response.parse()
            assert_matches_type(BatchProcessUploadedMemoriesResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_process_uploaded_memories(self, client: Memv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            client.upload.batch.with_raw_response.process_uploaded_memories(
                "",
            )


class TestAsyncBatch:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncMemv) -> None:
        batch = await async_client.upload.batch.create(
            files=[
                {
                    "file_name": "fileName",
                    "file_type": "fileType",
                }
            ],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchCreateResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncMemv) -> None:
        response = await async_client.upload.batch.with_raw_response.create(
            files=[
                {
                    "file_name": "fileName",
                    "file_type": "fileType",
                }
            ],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(BatchCreateResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncMemv) -> None:
        async with async_client.upload.batch.with_streaming_response.create(
            files=[
                {
                    "file_name": "fileName",
                    "file_type": "fileType",
                }
            ],
            space_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(BatchCreateResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncMemv) -> None:
        batch = await async_client.upload.batch.cancel(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchCancelResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncMemv) -> None:
        response = await async_client.upload.batch.with_raw_response.cancel(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(BatchCancelResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncMemv) -> None:
        async with async_client.upload.batch.with_streaming_response.cancel(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(BatchCancelResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.upload.batch.with_raw_response.cancel(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_status(self, async_client: AsyncMemv) -> None:
        batch = await async_client.upload.batch.get_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchGetStatusResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_status(self, async_client: AsyncMemv) -> None:
        response = await async_client.upload.batch.with_raw_response.get_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(BatchGetStatusResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_status(self, async_client: AsyncMemv) -> None:
        async with async_client.upload.batch.with_streaming_response.get_status(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(BatchGetStatusResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_status(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.upload.batch.with_raw_response.get_status(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_mark_file_uploaded(self, async_client: AsyncMemv) -> None:
        batch = await async_client.upload.batch.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
        )
        assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_mark_file_uploaded_with_all_params(self, async_client: AsyncMemv) -> None:
        batch = await async_client.upload.batch.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
            r2_key="r2Key",
        )
        assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_mark_file_uploaded(self, async_client: AsyncMemv) -> None:
        response = await async_client.upload.batch.with_raw_response.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_mark_file_uploaded(self, async_client: AsyncMemv) -> None:
        async with async_client.upload.batch.with_streaming_response.mark_file_uploaded(
            batch_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            index=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(BatchMarkFileUploadedResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_mark_file_uploaded(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.upload.batch.with_raw_response.mark_file_uploaded(
                batch_id="",
                index=0,
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_process_uploaded_memories(self, async_client: AsyncMemv) -> None:
        batch = await async_client.upload.batch.process_uploaded_memories(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )
        assert_matches_type(BatchProcessUploadedMemoriesResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_process_uploaded_memories(self, async_client: AsyncMemv) -> None:
        response = await async_client.upload.batch.with_raw_response.process_uploaded_memories(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        batch = await response.parse()
        assert_matches_type(BatchProcessUploadedMemoriesResponse, batch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_process_uploaded_memories(self, async_client: AsyncMemv) -> None:
        async with async_client.upload.batch.with_streaming_response.process_uploaded_memories(
            "182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            batch = await response.parse()
            assert_matches_type(BatchProcessUploadedMemoriesResponse, batch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_process_uploaded_memories(self, async_client: AsyncMemv) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `batch_id` but received ''"):
            await async_client.upload.batch.with_raw_response.process_uploaded_memories(
                "",
            )

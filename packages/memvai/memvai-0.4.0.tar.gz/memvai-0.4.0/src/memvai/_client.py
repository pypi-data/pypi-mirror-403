# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Mapping, cast
from typing_extensions import Self, Literal, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import MemvError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import files, graph, spaces, upload, videos, memories
    from .resources.files import FilesResource, AsyncFilesResource
    from .resources.graph import GraphResource, AsyncGraphResource
    from .resources.spaces import SpacesResource, AsyncSpacesResource
    from .resources.videos import VideosResource, AsyncVideosResource
    from .resources.memories import MemoriesResource, AsyncMemoriesResource
    from .resources.upload.upload import UploadResource, AsyncUploadResource
    from .types.upload.batch_get_status_response import Batch

__all__ = [
    "ENVIRONMENTS",
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Memv",
    "AsyncMemv",
    "Client",
    "AsyncClient",
]

ENVIRONMENTS: Dict[str, str] = {
    "production": "https://api.memv.ai/v1",
    "development": "https://devapi.memv.ai/v1",
    "local": "http://localhost:3000/v1",
}


class Memv(SyncAPIClient):
    # client options
    api_key: str

    _environment: Literal["production", "development", "local"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "development", "local"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Memv client instance.

        This automatically infers the `api_key` argument from the `MEMV_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("MEMV_API_KEY")
        if api_key is None:
            raise MemvError(
                "The api_key client option must be set either by passing api_key to the client or by setting the MEMV_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("MEMV_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `MEMV_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def spaces(self) -> SpacesResource:
        from .resources.spaces import SpacesResource

        return SpacesResource(self)

    @cached_property
    def memories(self) -> MemoriesResource:
        from .resources.memories import MemoriesResource

        return MemoriesResource(self)

    @cached_property
    def videos(self) -> VideosResource:
        from .resources.videos import VideosResource

        return VideosResource(self)

    @cached_property
    def files(self) -> FilesResource:
        from .resources.files import FilesResource

        return FilesResource(self)

    @cached_property
    def upload(self) -> UploadResource:
        from .resources.upload import UploadResource

        return UploadResource(self)

    @cached_property
    def graph(self) -> GraphResource:
        from .resources.graph import GraphResource

        return GraphResource(self)

    @cached_property
    def with_raw_response(self) -> MemvWithRawResponse:
        return MemvWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MemvWithStreamedResponse:
        return MemvWithStreamedResponse(self)

    def upload_files(
        self,
        space_id: str,
        files: "List[Union[str, Path]]",
        *,
        on_progress: "Callable[[int, int, str], None] | None" = None,
        wait_for_processing: bool = True,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> "Batch":
        """
        Upload multiple files to a memory space.

        This convenience method handles the full batch upload flow:
        1. Creates a batch with presigned URLs
        2. Uploads each file to its presigned URL
        3. Marks each file as uploaded
        4. Triggers AI processing
        5. Optionally polls until processing completes

        Args:
            space_id: The memory space ID to upload files to
            files: List of file paths to upload (max 5)
            on_progress: Optional callback(current, total, status)
            wait_for_processing: If True, polls until complete
            poll_interval: Seconds between status polls
            timeout: Max seconds to wait for processing

        Returns:
            Batch with the final state

        Example:
            ```python
            result = client.upload_files(
                space_id="abc-123",
                files=["meeting.mp4", "notes.pdf"],
                on_progress=lambda c, t, s: print(f"{c}/{t}: {s}")
            )
            ```
        """
        from ._helpers.batch_upload import upload_files as _upload_files

        return _upload_files(
            self,
            space_id,
            files,
            on_progress=on_progress,
            wait_for_processing=wait_for_processing,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "development", "local"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncMemv(AsyncAPIClient):
    # client options
    api_key: str

    _environment: Literal["production", "development", "local"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "development", "local"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncMemv client instance.

        This automatically infers the `api_key` argument from the `MEMV_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("MEMV_API_KEY")
        if api_key is None:
            raise MemvError(
                "The api_key client option must be set either by passing api_key to the client or by setting the MEMV_API_KEY environment variable"
            )
        self.api_key = api_key

        self._environment = environment

        base_url_env = os.environ.get("MEMV_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `MEMV_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def spaces(self) -> AsyncSpacesResource:
        from .resources.spaces import AsyncSpacesResource

        return AsyncSpacesResource(self)

    @cached_property
    def memories(self) -> AsyncMemoriesResource:
        from .resources.memories import AsyncMemoriesResource

        return AsyncMemoriesResource(self)

    @cached_property
    def videos(self) -> AsyncVideosResource:
        from .resources.videos import AsyncVideosResource

        return AsyncVideosResource(self)

    @cached_property
    def files(self) -> AsyncFilesResource:
        from .resources.files import AsyncFilesResource

        return AsyncFilesResource(self)

    @cached_property
    def upload(self) -> AsyncUploadResource:
        from .resources.upload import AsyncUploadResource

        return AsyncUploadResource(self)

    @cached_property
    def graph(self) -> AsyncGraphResource:
        from .resources.graph import AsyncGraphResource

        return AsyncGraphResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncMemvWithRawResponse:
        return AsyncMemvWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMemvWithStreamedResponse:
        return AsyncMemvWithStreamedResponse(self)

    async def upload_files(
        self,
        space_id: str,
        files: "List[Union[str, Path]]",
        *,
        on_progress: "Callable[[int, int, str], None] | None" = None,
        wait_for_processing: bool = True,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> "Batch":
        """
        Async version of upload_files.

        Upload multiple files to a memory space asynchronously.

        This convenience method handles the full batch upload flow:
        1. Creates a batch with presigned URLs
        2. Uploads each file to its presigned URL
        3. Marks each file as uploaded
        4. Triggers AI processing
        5. Optionally polls until processing completes

        Args:
            space_id: The memory space ID to upload files to
            files: List of file paths to upload (max 5)
            on_progress: Optional callback(current, total, status)
            wait_for_processing: If True, polls until complete
            poll_interval: Seconds between status polls
            timeout: Max seconds to wait for processing

        Returns:
            Batch with the final state

        Example:
            ```python
            result = await client.upload_files(
                space_id="abc-123",
                files=["meeting.mp4", "notes.pdf"],
            )
            ```
        """
        from ._helpers.batch_upload import async_upload_files as _async_upload_files

        return await _async_upload_files(
            self,
            space_id,
            files,
            on_progress=on_progress,
            wait_for_processing=wait_for_processing,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        environment: Literal["production", "development", "local"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class MemvWithRawResponse:
    _client: Memv

    def __init__(self, client: Memv) -> None:
        self._client = client

    @cached_property
    def spaces(self) -> spaces.SpacesResourceWithRawResponse:
        from .resources.spaces import SpacesResourceWithRawResponse

        return SpacesResourceWithRawResponse(self._client.spaces)

    @cached_property
    def memories(self) -> memories.MemoriesResourceWithRawResponse:
        from .resources.memories import MemoriesResourceWithRawResponse

        return MemoriesResourceWithRawResponse(self._client.memories)

    @cached_property
    def videos(self) -> videos.VideosResourceWithRawResponse:
        from .resources.videos import VideosResourceWithRawResponse

        return VideosResourceWithRawResponse(self._client.videos)

    @cached_property
    def files(self) -> files.FilesResourceWithRawResponse:
        from .resources.files import FilesResourceWithRawResponse

        return FilesResourceWithRawResponse(self._client.files)

    @cached_property
    def upload(self) -> upload.UploadResourceWithRawResponse:
        from .resources.upload import UploadResourceWithRawResponse

        return UploadResourceWithRawResponse(self._client.upload)

    @cached_property
    def graph(self) -> graph.GraphResourceWithRawResponse:
        from .resources.graph import GraphResourceWithRawResponse

        return GraphResourceWithRawResponse(self._client.graph)


class AsyncMemvWithRawResponse:
    _client: AsyncMemv

    def __init__(self, client: AsyncMemv) -> None:
        self._client = client

    @cached_property
    def spaces(self) -> spaces.AsyncSpacesResourceWithRawResponse:
        from .resources.spaces import AsyncSpacesResourceWithRawResponse

        return AsyncSpacesResourceWithRawResponse(self._client.spaces)

    @cached_property
    def memories(self) -> memories.AsyncMemoriesResourceWithRawResponse:
        from .resources.memories import AsyncMemoriesResourceWithRawResponse

        return AsyncMemoriesResourceWithRawResponse(self._client.memories)

    @cached_property
    def videos(self) -> videos.AsyncVideosResourceWithRawResponse:
        from .resources.videos import AsyncVideosResourceWithRawResponse

        return AsyncVideosResourceWithRawResponse(self._client.videos)

    @cached_property
    def files(self) -> files.AsyncFilesResourceWithRawResponse:
        from .resources.files import AsyncFilesResourceWithRawResponse

        return AsyncFilesResourceWithRawResponse(self._client.files)

    @cached_property
    def upload(self) -> upload.AsyncUploadResourceWithRawResponse:
        from .resources.upload import AsyncUploadResourceWithRawResponse

        return AsyncUploadResourceWithRawResponse(self._client.upload)

    @cached_property
    def graph(self) -> graph.AsyncGraphResourceWithRawResponse:
        from .resources.graph import AsyncGraphResourceWithRawResponse

        return AsyncGraphResourceWithRawResponse(self._client.graph)


class MemvWithStreamedResponse:
    _client: Memv

    def __init__(self, client: Memv) -> None:
        self._client = client

    @cached_property
    def spaces(self) -> spaces.SpacesResourceWithStreamingResponse:
        from .resources.spaces import SpacesResourceWithStreamingResponse

        return SpacesResourceWithStreamingResponse(self._client.spaces)

    @cached_property
    def memories(self) -> memories.MemoriesResourceWithStreamingResponse:
        from .resources.memories import MemoriesResourceWithStreamingResponse

        return MemoriesResourceWithStreamingResponse(self._client.memories)

    @cached_property
    def videos(self) -> videos.VideosResourceWithStreamingResponse:
        from .resources.videos import VideosResourceWithStreamingResponse

        return VideosResourceWithStreamingResponse(self._client.videos)

    @cached_property
    def files(self) -> files.FilesResourceWithStreamingResponse:
        from .resources.files import FilesResourceWithStreamingResponse

        return FilesResourceWithStreamingResponse(self._client.files)

    @cached_property
    def upload(self) -> upload.UploadResourceWithStreamingResponse:
        from .resources.upload import UploadResourceWithStreamingResponse

        return UploadResourceWithStreamingResponse(self._client.upload)

    @cached_property
    def graph(self) -> graph.GraphResourceWithStreamingResponse:
        from .resources.graph import GraphResourceWithStreamingResponse

        return GraphResourceWithStreamingResponse(self._client.graph)


class AsyncMemvWithStreamedResponse:
    _client: AsyncMemv

    def __init__(self, client: AsyncMemv) -> None:
        self._client = client

    @cached_property
    def spaces(self) -> spaces.AsyncSpacesResourceWithStreamingResponse:
        from .resources.spaces import AsyncSpacesResourceWithStreamingResponse

        return AsyncSpacesResourceWithStreamingResponse(self._client.spaces)

    @cached_property
    def memories(self) -> memories.AsyncMemoriesResourceWithStreamingResponse:
        from .resources.memories import AsyncMemoriesResourceWithStreamingResponse

        return AsyncMemoriesResourceWithStreamingResponse(self._client.memories)

    @cached_property
    def videos(self) -> videos.AsyncVideosResourceWithStreamingResponse:
        from .resources.videos import AsyncVideosResourceWithStreamingResponse

        return AsyncVideosResourceWithStreamingResponse(self._client.videos)

    @cached_property
    def files(self) -> files.AsyncFilesResourceWithStreamingResponse:
        from .resources.files import AsyncFilesResourceWithStreamingResponse

        return AsyncFilesResourceWithStreamingResponse(self._client.files)

    @cached_property
    def upload(self) -> upload.AsyncUploadResourceWithStreamingResponse:
        from .resources.upload import AsyncUploadResourceWithStreamingResponse

        return AsyncUploadResourceWithStreamingResponse(self._client.upload)

    @cached_property
    def graph(self) -> graph.AsyncGraphResourceWithStreamingResponse:
        from .resources.graph import AsyncGraphResourceWithStreamingResponse

        return AsyncGraphResourceWithStreamingResponse(self._client.graph)


Client = Memv

AsyncClient = AsyncMemv

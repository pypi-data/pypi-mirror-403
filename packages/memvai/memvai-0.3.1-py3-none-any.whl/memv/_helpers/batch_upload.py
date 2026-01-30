"""
Custom helper for batch file uploads.

This module provides convenience functions that orchestrate the multi-step
batch upload process into a single function call.
"""

from __future__ import annotations

import time
import mimetypes
from typing import TYPE_CHECKING, List, Union, Callable, Optional
from pathlib import Path

import httpx

from ..types.upload.batch_create_params import File as FileParam

if TYPE_CHECKING:
    from .._client import Memv, AsyncMemv
    from ..types.upload.batch_get_status_response import Batch

__all__ = ["upload_files", "async_upload_files"]


# MIME type mappings for common file types
MIME_TYPE_MAP = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".csv": "text/csv",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def _get_mime_type(file_path: Path) -> str:
    """Get MIME type for a file, with fallback to application/octet-stream."""
    suffix = file_path.suffix.lower()
    if suffix in MIME_TYPE_MAP:
        return MIME_TYPE_MAP[suffix]

    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def _prepare_file_infos(files: List[Union[str, Path]]) -> List[FileParam]:
    """Prepare file metadata for batch creation."""
    file_infos: List[FileParam] = []
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_infos.append(
            FileParam(
                file_name=path.name,
                file_size=path.stat().st_size,
                file_type=_get_mime_type(path),
            )
        )
    return file_infos


def upload_files(
    client: "Memv",
    space_id: str,
    files: List[Union[str, Path]],
    *,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
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
        client: The Memv client instance
        space_id: The memory space ID to upload files to
        files: List of file paths (str or Path) to upload. Max 5 files per batch.
        on_progress: Optional callback function called with (current, total, status)
            - current: Number of files processed so far
            - total: Total number of files
            - status: One of "creating_batch", "uploading", "uploaded", "processing",
                      "completed", "partial", "failed"
        wait_for_processing: If True (default), polls until processing completes.
            If False, returns immediately after triggering processing.
        poll_interval: Seconds between status polls (default: 2.0)
        timeout: Maximum seconds to wait for processing (default: 300.0)

    Returns:
        Batch object with the final state of the batch

    Raises:
        FileNotFoundError: If any file in the list doesn't exist
        ValueError: If more than 5 files are provided or no files are provided
        TimeoutError: If processing doesn't complete within timeout
        httpx.HTTPStatusError: If file upload to presigned URL fails

    Example:
        ```python
        from memv import Memv

        client = Memv(api_key="memv_...")

        # Simple upload
        result = client.upload_files(
            space_id="abc-123-def",
            files=["meeting.mp4", "notes.pdf"],
        )

        # Upload with progress tracking
        def on_progress(current, total, status):
            print(f"[{current}/{total}] {status}")

        result = client.upload_files(
            space_id="abc-123-def",
            files=["meeting.mp4", "notes.pdf", "diagram.png"],
            on_progress=on_progress,
        )

        print(f"Processed {result.processed_files}/{result.total_files} files")
        ```
    """
    # Validate inputs
    if len(files) > 5:
        raise ValueError("Maximum 5 files per batch. Split into multiple batches.")

    if len(files) == 0:
        raise ValueError("At least one file is required.")

    # Prepare file metadata
    file_infos = _prepare_file_infos(files)
    file_paths = [Path(f) for f in files]

    # Step 1: Create batch
    if on_progress:
        on_progress(0, len(files), "creating_batch")

    batch_response = client.upload.batch.create(
        space_id=space_id,
        files=file_infos,
    )
    batch_id = batch_response.batch_id

    if not batch_id:
        raise ValueError("Failed to create batch: no batch_id returned")

    if not batch_response.uploads:
        raise ValueError("Failed to create batch: no upload URLs returned")

    # Step 2 & 3: Upload each file and mark as uploaded
    with httpx.Client(timeout=60.0) as http_client:
        for i, (file_path, upload_info) in enumerate(zip(file_paths, batch_response.uploads)):
            if on_progress:
                on_progress(i, len(files), "uploading")

            if not upload_info.upload_url:
                raise ValueError(f"No upload URL for file at index {i}")

            # Upload to presigned URL
            with open(file_path, "rb") as f:
                response = http_client.put(
                    upload_info.upload_url,
                    content=f.read(),
                    headers={"Content-Type": file_infos[i]["file_type"]},
                )
                response.raise_for_status()

            # Mark file as uploaded
            client.upload.batch.mark_file_uploaded(batch_id, index=i)

            if on_progress:
                on_progress(i + 1, len(files), "uploaded")

    # Step 4: Trigger processing
    if on_progress:
        on_progress(len(files), len(files), "processing")

    client.upload.batch.process_uploaded_memories(batch_id)

    # Step 5: Poll for completion (optional)
    if not wait_for_processing:
        status_response = client.upload.batch.get_status(batch_id)
        if not status_response.batch:
            raise ValueError("Failed to get batch status")
        return status_response.batch

    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Batch processing did not complete within {timeout} seconds. " f"Batch ID: {batch_id}"
            )

        status_response = client.upload.batch.get_status(batch_id)
        if not status_response.batch:
            raise ValueError("Failed to get batch status")

        batch_status = status_response.batch

        if batch_status.status in ("completed", "partial", "failed"):
            if on_progress:
                on_progress(len(files), len(files), batch_status.status)
            return batch_status

        time.sleep(poll_interval)


async def async_upload_files(
    client: "AsyncMemv",
    space_id: str,
    files: List[Union[str, Path]],
    *,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
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
        client: The AsyncMemv client instance
        space_id: The memory space ID to upload files to
        files: List of file paths (str or Path) to upload. Max 5 files per batch.
        on_progress: Optional callback function called with (current, total, status)
            - current: Number of files processed so far
            - total: Total number of files
            - status: One of "creating_batch", "uploading", "uploaded", "processing",
                      "completed", "partial", "failed"
        wait_for_processing: If True (default), polls until processing completes.
            If False, returns immediately after triggering processing.
        poll_interval: Seconds between status polls (default: 2.0)
        timeout: Maximum seconds to wait for processing (default: 300.0)

    Returns:
        Batch object with the final state of the batch

    Raises:
        FileNotFoundError: If any file in the list doesn't exist
        ValueError: If more than 5 files are provided or no files are provided
        TimeoutError: If processing doesn't complete within timeout
        httpx.HTTPStatusError: If file upload to presigned URL fails

    Example:
        ```python
        import asyncio
        from memv import AsyncMemv

        async def main():
            client = AsyncMemv(api_key="memv_...")

            result = await client.upload_files(
                space_id="abc-123-def",
                files=["video.mp4", "audio.mp3"],
            )
            print(f"Done: {result.status}")

        asyncio.run(main())
        ```
    """
    import asyncio

    # Validate inputs
    if len(files) > 5:
        raise ValueError("Maximum 5 files per batch. Split into multiple batches.")

    if len(files) == 0:
        raise ValueError("At least one file is required.")

    # Prepare file metadata
    file_infos = _prepare_file_infos(files)
    file_paths = [Path(f) for f in files]

    # Step 1: Create batch
    if on_progress:
        on_progress(0, len(files), "creating_batch")

    batch_response = await client.upload.batch.create(
        space_id=space_id,
        files=file_infos,
    )
    batch_id = batch_response.batch_id

    if not batch_id:
        raise ValueError("Failed to create batch: no batch_id returned")

    if not batch_response.uploads:
        raise ValueError("Failed to create batch: no upload URLs returned")

    # Step 2 & 3: Upload each file and mark as uploaded
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        for i, (file_path, upload_info) in enumerate(zip(file_paths, batch_response.uploads)):
            if on_progress:
                on_progress(i, len(files), "uploading")

            if not upload_info.upload_url:
                raise ValueError(f"No upload URL for file at index {i}")

            # Upload to presigned URL
            with open(file_path, "rb") as f:
                content = f.read()

            response = await http_client.put(
                upload_info.upload_url,
                content=content,
                headers={"Content-Type": file_infos[i]["file_type"]},
            )
            response.raise_for_status()

            # Mark file as uploaded
            await client.upload.batch.mark_file_uploaded(batch_id, index=i)

            if on_progress:
                on_progress(i + 1, len(files), "uploaded")

    # Step 4: Trigger processing
    if on_progress:
        on_progress(len(files), len(files), "processing")

    await client.upload.batch.process_uploaded_memories(batch_id)

    # Step 5: Poll for completion (optional)
    if not wait_for_processing:
        status_response = await client.upload.batch.get_status(batch_id)
        if not status_response.batch:
            raise ValueError("Failed to get batch status")
        return status_response.batch

    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Batch processing did not complete within {timeout} seconds. " f"Batch ID: {batch_id}"
            )

        status_response = await client.upload.batch.get_status(batch_id)
        if not status_response.batch:
            raise ValueError("Failed to get batch status")

        batch_status = status_response.batch

        if batch_status.status in ("completed", "partial", "failed"):
            if on_progress:
                on_progress(len(files), len(files), batch_status.status)
            return batch_status

        await asyncio.sleep(poll_interval)

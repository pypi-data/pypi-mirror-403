# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BatchProcessUploadedMemoriesResponse"]


class BatchProcessUploadedMemoriesResponse(BaseModel):
    batch_id: Optional[str] = FieldInfo(alias="batchId", default=None)

    files_to_process: Optional[int] = FieldInfo(alias="filesToProcess", default=None)

    message: Optional[str] = None

    skipped_files: Optional[int] = FieldInfo(alias="skippedFiles", default=None)

    status_url: Optional[str] = FieldInfo(alias="statusUrl", default=None)

    success: Optional[bool] = None

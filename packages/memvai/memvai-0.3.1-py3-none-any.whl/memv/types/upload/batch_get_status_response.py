# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BatchGetStatusResponse", "Batch", "BatchFile"]


class BatchFile(BaseModel):
    error: Optional[str] = None

    file_name: Optional[str] = FieldInfo(alias="fileName", default=None)

    file_size: Optional[int] = FieldInfo(alias="fileSize", default=None)

    file_type: Optional[str] = FieldInfo(alias="fileType", default=None)

    index: Optional[int] = None

    process_status: Optional[Literal["pending", "processing", "completed", "failed", "skipped"]] = FieldInfo(
        alias="processStatus", default=None
    )

    result_id: Optional[str] = FieldInfo(alias="resultId", default=None)
    """Memory ID (video or file) after processing"""

    upload_status: Optional[Literal["pending", "uploaded"]] = FieldInfo(alias="uploadStatus", default=None)


class Batch(BaseModel):
    id: Optional[str] = None

    completed_at: Optional[datetime] = FieldInfo(alias="completedAt", default=None)

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)

    current_file: Optional[str] = FieldInfo(alias="currentFile", default=None)

    expires_at: Optional[datetime] = FieldInfo(alias="expiresAt", default=None)

    failed_files: Optional[int] = FieldInfo(alias="failedFiles", default=None)

    files: Optional[List[BatchFile]] = None

    processed_files: Optional[int] = FieldInfo(alias="processedFiles", default=None)

    space_id: Optional[str] = FieldInfo(alias="spaceId", default=None)

    status: Optional[Literal["uploading", "processing", "completed", "partial", "cancelled", "failed"]] = None

    total_files: Optional[int] = FieldInfo(alias="totalFiles", default=None)

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)

    uploaded_files: Optional[int] = FieldInfo(alias="uploadedFiles", default=None)


class BatchGetStatusResponse(BaseModel):
    batch: Optional[Batch] = None

    success: Optional[bool] = None

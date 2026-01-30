# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BatchCreateResponse", "Upload"]


class Upload(BaseModel):
    expires_at: Optional[datetime] = FieldInfo(alias="expiresAt", default=None)

    file_name: Optional[str] = FieldInfo(alias="fileName", default=None)

    index: Optional[int] = None

    r2_key: Optional[str] = FieldInfo(alias="r2Key", default=None)

    upload_url: Optional[str] = FieldInfo(alias="uploadUrl", default=None)
    """Presigned URL for direct upload"""


class BatchCreateResponse(BaseModel):
    batch_id: Optional[str] = FieldInfo(alias="batchId", default=None)

    expires_at: Optional[datetime] = FieldInfo(alias="expiresAt", default=None)

    success: Optional[bool] = None

    uploads: Optional[List[Upload]] = None

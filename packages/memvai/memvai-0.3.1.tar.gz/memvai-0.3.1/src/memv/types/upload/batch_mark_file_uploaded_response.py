# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BatchMarkFileUploadedResponse"]


class BatchMarkFileUploadedResponse(BaseModel):
    success: Optional[bool] = None

    total_files: Optional[int] = FieldInfo(alias="totalFiles", default=None)

    uploaded_files: Optional[int] = FieldInfo(alias="uploadedFiles", default=None)

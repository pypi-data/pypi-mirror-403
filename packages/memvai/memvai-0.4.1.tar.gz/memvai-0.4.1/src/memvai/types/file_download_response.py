# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["FileDownloadResponse"]


class FileDownloadResponse(BaseModel):
    download_url: Optional[str] = FieldInfo(alias="downloadUrl", default=None)

    expires_in: Optional[int] = FieldInfo(alias="expiresIn", default=None)

    filename: Optional[str] = None

    mime_type: Optional[str] = FieldInfo(alias="mimeType", default=None)

    success: Optional[bool] = None

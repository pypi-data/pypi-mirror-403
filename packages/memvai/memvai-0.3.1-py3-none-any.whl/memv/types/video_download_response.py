# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["VideoDownloadResponse"]


class VideoDownloadResponse(BaseModel):
    download_url: Optional[str] = FieldInfo(alias="downloadUrl", default=None)

    expires_in: Optional[int] = FieldInfo(alias="expiresIn", default=None)
    """URL expiry in seconds"""

    filename: Optional[str] = None

    success: Optional[bool] = None

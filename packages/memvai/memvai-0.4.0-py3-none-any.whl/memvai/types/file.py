# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["File"]


class File(BaseModel):
    id: Optional[str] = None

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)

    filename: Optional[str] = None

    file_size: Optional[int] = FieldInfo(alias="fileSize", default=None)

    file_type: Optional[Literal["audio", "image", "text", "document"]] = FieldInfo(alias="fileType", default=None)

    mime_type: Optional[str] = FieldInfo(alias="mimeType", default=None)

    original_name: Optional[str] = FieldInfo(alias="originalName", default=None)

    processed_at: Optional[datetime] = FieldInfo(alias="processedAt", default=None)

    space_id: Optional[str] = FieldInfo(alias="spaceId", default=None)

    space_name: Optional[str] = FieldInfo(alias="spaceName", default=None)

    status: Optional[Literal["processing", "completed", "failed"]] = None

    summary: Optional[str] = None

    topics: Optional[List[str]] = None

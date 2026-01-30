# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .pagination import Pagination

__all__ = ["VideoListResponse", "Video"]


class Video(BaseModel):
    id: Optional[str] = None

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)

    duration: Optional[float] = None

    filename: Optional[str] = None

    file_size: Optional[int] = FieldInfo(alias="fileSize", default=None)

    language: Optional[str] = None

    original_name: Optional[str] = FieldInfo(alias="originalName", default=None)

    playback_url: Optional[str] = FieldInfo(alias="playbackUrl", default=None)

    processed_at: Optional[datetime] = FieldInfo(alias="processedAt", default=None)

    space_id: Optional[str] = FieldInfo(alias="spaceId", default=None)

    space_name: Optional[str] = FieldInfo(alias="spaceName", default=None)

    status: Optional[Literal["processing", "completed", "failed"]] = None

    summary: Optional[str] = None

    thumbnail_url: Optional[str] = FieldInfo(alias="thumbnailUrl", default=None)

    topics: Optional[List[str]] = None


class VideoListResponse(BaseModel):
    pagination: Optional[Pagination] = None

    success: Optional[bool] = None

    videos: Optional[List[Video]] = None

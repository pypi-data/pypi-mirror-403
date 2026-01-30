# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["VideoListParams"]


class VideoListParams(TypedDict, total=False):
    limit: int

    offset: int

    space_id: Annotated[str, PropertyInfo(alias="spaceId")]
    """Filter by space"""

    status: Literal["processing", "completed", "failed"]
    """Filter by status"""

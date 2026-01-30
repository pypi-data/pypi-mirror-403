# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["BatchCreateParams", "File"]


class BatchCreateParams(TypedDict, total=False):
    files: Required[Iterable[File]]

    space_id: Required[Annotated[str, PropertyInfo(alias="spaceId")]]


class File(TypedDict, total=False):
    file_name: Required[Annotated[str, PropertyInfo(alias="fileName")]]

    file_type: Required[Annotated[str, PropertyInfo(alias="fileType")]]
    """MIME type (e.g., video/mp4, image/png)"""

    file_size: Annotated[int, PropertyInfo(alias="fileSize")]

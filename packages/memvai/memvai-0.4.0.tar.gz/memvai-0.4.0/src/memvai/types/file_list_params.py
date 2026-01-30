# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["FileListParams"]


class FileListParams(TypedDict, total=False):
    file_type: Annotated[Literal["audio", "image", "text", "document"], PropertyInfo(alias="fileType")]

    limit: int

    offset: int

    space_id: Annotated[str, PropertyInfo(alias="spaceId")]

    status: Literal["processing", "completed", "failed"]

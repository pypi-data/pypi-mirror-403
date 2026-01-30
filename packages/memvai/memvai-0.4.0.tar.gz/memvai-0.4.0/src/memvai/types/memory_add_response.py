# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["MemoryAddResponse"]


class MemoryAddResponse(BaseModel):
    memories_added: Optional[int] = FieldInfo(alias="memoriesAdded", default=None)

    space_id: Optional[str] = FieldInfo(alias="spaceId", default=None)

    success: Optional[bool] = None

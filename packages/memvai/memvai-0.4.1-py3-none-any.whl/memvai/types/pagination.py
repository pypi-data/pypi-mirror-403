# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Pagination"]


class Pagination(BaseModel):
    has_more: Optional[bool] = FieldInfo(alias="hasMore", default=None)

    limit: Optional[int] = None

    offset: Optional[int] = None

    total: Optional[int] = None

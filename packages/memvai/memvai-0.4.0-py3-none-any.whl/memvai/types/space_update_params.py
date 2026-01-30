# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["SpaceUpdateParams"]


class SpaceUpdateParams(TypedDict, total=False):
    space_id: Required[Annotated[str, PropertyInfo(alias="spaceId")]]

    description: Optional[str]

    is_public: Annotated[bool, PropertyInfo(alias="isPublic")]

    name: str

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from . import space
from .._models import BaseModel

__all__ = ["SpaceGetStatsResponse", "Space", "SpaceModalities"]


class SpaceModalities(BaseModel):
    audio: Optional[int] = None

    documents: Optional[int] = None

    images: Optional[int] = None

    video: Optional[int] = None


class Space(space.Space):
    modalities: Optional[SpaceModalities] = None


class SpaceGetStatsResponse(BaseModel):
    spaces: Optional[List[Space]] = None

    success: Optional[bool] = None

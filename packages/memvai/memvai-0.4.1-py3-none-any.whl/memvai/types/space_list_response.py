# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .space import Space
from .._models import BaseModel

__all__ = ["SpaceListResponse"]


class SpaceListResponse(BaseModel):
    spaces: Optional[List[Space]] = None

    success: Optional[bool] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .space import Space
from .._models import BaseModel

__all__ = ["SpaceUpdateResponse"]


class SpaceUpdateResponse(BaseModel):
    space: Optional[Space] = None

    success: Optional[bool] = None

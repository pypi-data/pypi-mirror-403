# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .file import File
from .._models import BaseModel
from .pagination import Pagination

__all__ = ["FileListResponse"]


class FileListResponse(BaseModel):
    files: Optional[List[File]] = None

    pagination: Optional[Pagination] = None

    success: Optional[bool] = None

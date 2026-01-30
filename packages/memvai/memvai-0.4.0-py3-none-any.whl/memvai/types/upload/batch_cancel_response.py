# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["BatchCancelResponse"]


class BatchCancelResponse(BaseModel):
    cleaned_up_files: Optional[int] = FieldInfo(alias="cleanedUpFiles", default=None)

    message: Optional[str] = None

    success: Optional[bool] = None

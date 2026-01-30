# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from . import file
from .._models import BaseModel

__all__ = ["FileRetrieveResponse", "File"]


class File(file.File):
    description: Optional[str] = None

    entities: Optional[List[str]] = None

    extracted_text: Optional[str] = FieldInfo(alias="extractedText", default=None)

    key_points: Optional[List[str]] = FieldInfo(alias="keyPoints", default=None)

    transcript: Optional[str] = None


class FileRetrieveResponse(BaseModel):
    file: Optional[File] = None

    success: Optional[bool] = None

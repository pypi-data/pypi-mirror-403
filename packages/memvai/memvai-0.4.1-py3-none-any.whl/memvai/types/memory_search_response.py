# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["MemorySearchResponse", "Result"]


class Result(BaseModel):
    fact: Optional[str] = None
    """The memory content/fact extracted from the knowledge graph"""

    file_name: Optional[str] = FieldInfo(alias="fileName", default=None)
    """Original file name if memory came from uploaded content"""

    name: Optional[str] = None
    """Relationship type in the knowledge graph (e.g., "HAS_NAME", "PREFERS")"""

    source_description: Optional[str] = FieldInfo(alias="sourceDescription", default=None)
    """Source of this memory"""

    uuid: Optional[str] = None
    """Unique identifier for this memory"""

    valid_at: Optional[datetime] = FieldInfo(alias="validAt", default=None)
    """Timestamp when this memory was recorded"""


class MemorySearchResponse(BaseModel):
    results: Optional[List[Result]] = None

    success: Optional[bool] = None

    total_results: Optional[int] = FieldInfo(alias="totalResults", default=None)

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["MemoryAddParams", "Memory", "MemoryMetadata"]


class MemoryAddParams(TypedDict, total=False):
    memories: Required[Iterable[Memory]]

    space_id: Required[Annotated[str, PropertyInfo(alias="spaceId")]]
    """The memory space to add memories to"""


class MemoryMetadata(TypedDict, total=False):
    file_name: Annotated[str, PropertyInfo(alias="fileName")]

    timestamp: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]


class Memory(TypedDict, total=False):
    content: Required[str]
    """The memory content to store"""

    metadata: MemoryMetadata

    name: str
    """Optional identifier for the memory"""

    role: str
    """Role of the memory source (e.g., "User", "System")"""

    source_description: Annotated[str, PropertyInfo(alias="sourceDescription")]
    """Description of where this memory came from"""

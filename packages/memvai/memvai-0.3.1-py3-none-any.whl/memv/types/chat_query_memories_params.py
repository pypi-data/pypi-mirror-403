# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ChatQueryMemoriesParams", "Message"]


class ChatQueryMemoriesParams(TypedDict, total=False):
    group_id: Required[Annotated[str, PropertyInfo(alias="groupId")]]
    """Memory space ID to query"""

    messages: Required[Iterable[Message]]

    add_memory_mode: Annotated[bool, PropertyInfo(alias="addMemoryMode")]
    """When true, also adds the query context as a new memory"""


class Message(TypedDict, total=False):
    content: Required[str]

    role: Required[Literal["user", "assistant"]]

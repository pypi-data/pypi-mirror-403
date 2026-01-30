# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ChatQueryMemoriesResponse", "ToolInvocation"]


class ToolInvocation(BaseModel):
    result: Optional[object] = None

    tool_name: Optional[str] = FieldInfo(alias="toolName", default=None)


class ChatQueryMemoriesResponse(BaseModel):
    content: Optional[str] = None

    tool_invocations: Optional[List[ToolInvocation]] = FieldInfo(alias="toolInvocations", default=None)

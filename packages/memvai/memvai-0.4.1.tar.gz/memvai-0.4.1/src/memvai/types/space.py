# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Space"]


class Space(BaseModel):
    id: Optional[str] = None

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)

    description: Optional[str] = None

    is_public: Optional[bool] = FieldInfo(alias="isPublic", default=None)

    name: Optional[str] = None

    project_id: Optional[str] = FieldInfo(alias="projectId", default=None)

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)

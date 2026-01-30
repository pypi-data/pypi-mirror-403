# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["BatchMarkFileUploadedParams"]


class BatchMarkFileUploadedParams(TypedDict, total=False):
    index: Required[int]
    """File index in the batch (0-based)"""

    r2_key: Annotated[str, PropertyInfo(alias="r2Key")]
    """R2 storage key (optional, for verification)"""

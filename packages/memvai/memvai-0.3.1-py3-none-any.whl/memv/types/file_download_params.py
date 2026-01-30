# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["FileDownloadParams"]


class FileDownloadParams(TypedDict, total=False):
    return_url: Annotated[bool, PropertyInfo(alias="returnUrl")]

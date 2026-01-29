# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._types import FileTypes
from ..._utils import PropertyInfo

__all__ = ["FileUpdateParams"]


class FileUpdateParams(TypedDict, total=False):
    planned_date: Annotated[str, PropertyInfo(alias="plannedDate")]
    """Optional. Date the workout is planned to be done. Format is YYYY-MM-DD"""

    file: FileTypes
    """A workout file. Filename should have one of the following extensions: .fit .zwo"""

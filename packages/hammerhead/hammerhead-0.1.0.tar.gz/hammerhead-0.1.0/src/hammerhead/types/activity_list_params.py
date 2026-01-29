# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ActivityListParams"]


class ActivityListParams(TypedDict, total=False):
    page: int
    """Requested page of activities"""

    per_page: Annotated[int, PropertyInfo(alias="perPage")]
    """Number of activities per page"""

    start_date: Annotated[Union[str, date], PropertyInfo(alias="startDate", format="iso8601")]
    """A starting date in the form `YYYY-MM-DD`"""

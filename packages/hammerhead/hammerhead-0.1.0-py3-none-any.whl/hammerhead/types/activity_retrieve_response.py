# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .activity_summary import ActivitySummary

__all__ = ["ActivityRetrieveResponse"]


class ActivityRetrieveResponse(ActivitySummary):
    activity_type: Optional[Literal["RIDE", "EBIKE", "MOUNTAIN_BIKE", "GRAVEL", "EMOUNTAIN_BIKE", "VELOMOBILE"]] = (
        FieldInfo(alias="activityType", default=None)
    )

    description: Optional[str] = None

    polyline: Optional[str] = None

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)

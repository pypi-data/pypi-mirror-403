# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["Workout"]


class Workout(BaseModel):
    id: Optional[str] = None

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)

    description: Optional[str] = None

    name: Optional[str] = None

    planned_date: Optional[str] = FieldInfo(alias="plannedDate", default=None)

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)

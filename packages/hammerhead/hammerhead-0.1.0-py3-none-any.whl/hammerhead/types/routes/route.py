# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..route_summary import RouteSummary

__all__ = ["Route"]


class Route(RouteSummary):
    polyline: Optional[str] = None

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)

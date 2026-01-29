# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .pagination import Pagination
from .route_summary import RouteSummary

__all__ = ["RouteListResponse"]


class RouteListResponse(Pagination):
    data: Optional[List[RouteSummary]] = None

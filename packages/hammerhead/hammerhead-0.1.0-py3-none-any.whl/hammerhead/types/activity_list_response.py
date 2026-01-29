# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .pagination import Pagination
from .activity_summary import ActivitySummary

__all__ = ["ActivityListResponse"]


class ActivityListResponse(Pagination):
    data: Optional[List[ActivitySummary]] = None

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Pagination"]


class Pagination(BaseModel):
    current_page: Optional[int] = FieldInfo(alias="currentPage", default=None)
    """Current page number"""

    per_page: Optional[int] = FieldInfo(alias="perPage", default=None)
    """Number of items per page"""

    total_items: Optional[int] = FieldInfo(alias="totalItems", default=None)
    """Total paginated items"""

    total_pages: Optional[int] = FieldInfo(alias="totalPages", default=None)
    """Total number of pages"""

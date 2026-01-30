# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["Pagination"]


class Pagination(BaseModel):
    """Pagination metadata"""

    page: float
    """Current page number"""

    page_size: float
    """Number of items per page"""

    total_items: float
    """Total number of items"""

    total_pages: float
    """Total number of pages"""

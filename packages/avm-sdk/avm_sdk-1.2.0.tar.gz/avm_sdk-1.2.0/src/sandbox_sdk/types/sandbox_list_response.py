# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .sandbox import Sandbox
from .._models import BaseModel
from .pagination import Pagination

__all__ = ["SandboxListResponse"]


class SandboxListResponse(BaseModel):
    data: List[Sandbox]
    """Array of sandboxes"""

    pagination: Pagination
    """Pagination metadata"""

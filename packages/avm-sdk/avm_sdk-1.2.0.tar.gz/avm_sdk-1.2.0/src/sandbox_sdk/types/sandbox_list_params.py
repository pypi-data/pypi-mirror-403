# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["SandboxListParams"]


class SandboxListParams(TypedDict, total=False):
    page: float
    """Page number"""

    page_size: float
    """Page size"""

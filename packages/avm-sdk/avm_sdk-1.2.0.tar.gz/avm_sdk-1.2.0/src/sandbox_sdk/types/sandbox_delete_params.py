# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["SandboxDeleteParams"]


class SandboxDeleteParams(TypedDict, total=False):
    create_snapshot: bool
    """Create snapshot before deleting storage"""

    keep_storage: bool
    """Keep storage after deletion (default: false - storage deleted)"""

    snapshot_name: str
    """Custom name for the snapshot"""

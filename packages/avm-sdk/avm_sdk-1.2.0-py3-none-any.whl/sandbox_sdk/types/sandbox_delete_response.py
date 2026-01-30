# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["SandboxDeleteResponse"]


class SandboxDeleteResponse(BaseModel):
    id: str

    message: str

    snapshot_created: Optional[bool] = None
    """Whether snapshot was created"""

    snapshot_name: Optional[str] = None
    """Name of created snapshot"""

    storage_deleted: Optional[bool] = None
    """Whether storage was deleted"""

    storage_name: Optional[str] = None
    """Name of deleted storage"""

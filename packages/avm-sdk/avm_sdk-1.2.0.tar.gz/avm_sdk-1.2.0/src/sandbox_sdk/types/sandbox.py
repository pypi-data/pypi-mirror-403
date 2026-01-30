# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["Sandbox"]


class Sandbox(BaseModel):
    id: str
    """Sandbox ID"""

    cpu: float
    """CPU count"""

    created_at: str
    """Creation timestamp"""

    disk_size: float
    """Disk size in GB"""

    memory: float
    """Memory size in MB"""

    name: str
    """Sandbox name"""

    status: str
    """Sandbox status"""

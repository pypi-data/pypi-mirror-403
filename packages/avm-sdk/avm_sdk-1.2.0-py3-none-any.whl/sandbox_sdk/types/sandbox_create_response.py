# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .sandbox import Sandbox

__all__ = ["SandboxCreateResponse"]


class SandboxCreateResponse(Sandbox):
    id: str  # type: ignore
    """Sandbox ID"""

    cpu: float  # type: ignore
    """CPU count (API units, minimum 1)"""

    created_at: str  # type: ignore
    """Creation timestamp"""

    memory: float  # type: ignore
    """Memory size in MiB"""

    name: str  # type: ignore
    """Sandbox name"""

    status: str  # type: ignore
    """Sandbox status"""

    storage: float
    """Storage size in GB"""

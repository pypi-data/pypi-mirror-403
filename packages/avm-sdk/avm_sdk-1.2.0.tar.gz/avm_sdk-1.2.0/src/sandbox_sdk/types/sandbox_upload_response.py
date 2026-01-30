# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["SandboxUploadResponse"]


class SandboxUploadResponse(BaseModel):
    message: str
    """Success message"""

    path: str
    """Destination path where file was uploaded"""

    size: int
    """File size in bytes"""

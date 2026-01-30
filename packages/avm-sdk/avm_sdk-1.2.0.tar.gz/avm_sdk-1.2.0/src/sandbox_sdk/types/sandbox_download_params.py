# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SandboxDownloadParams"]


class SandboxDownloadParams(TypedDict, total=False):
    path: Required[str]
    """File path in sandbox (e.g., /data/myfile.txt)"""

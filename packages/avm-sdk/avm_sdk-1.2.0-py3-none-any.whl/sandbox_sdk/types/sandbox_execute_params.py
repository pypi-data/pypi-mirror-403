# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["SandboxExecuteParams"]


class SandboxExecuteParams(TypedDict, total=False):
    command: Required[str]
    """
    Command to execute (full CLI command, supports shell features like redirection,
    pipes, etc.)
    """

    env: Dict[str, str]
    """Environment variables"""

    api_timeout: Annotated[int, PropertyInfo(alias="timeout")]
    """Execution timeout in seconds"""

    working_dir: str
    """Working directory for execution"""

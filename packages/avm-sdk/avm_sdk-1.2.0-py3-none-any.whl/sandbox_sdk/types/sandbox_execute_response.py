# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["SandboxExecuteResponse"]


class SandboxExecuteResponse(BaseModel):
    id: str
    """Execution ID"""

    completed_at: str
    """Execution completion timestamp"""

    created_at: str
    """Execution start timestamp"""

    execution_time_ms: int
    """Execution time in milliseconds"""

    exit_code: int
    """Exit code"""

    status: Literal["running", "completed", "timeout", "error"]
    """Execution status"""

    stderr: str
    """Standard error output"""

    stdout: str
    """Standard output"""

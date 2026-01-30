# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import TypedDict

__all__ = ["SandboxCreateParams", "Resources"]


class SandboxCreateParams(TypedDict, total=False):
    env_vars: Dict[str, str]
    """Environment variables"""

    image: str
    """Docker image name (e.g., avmcodes/avm-default-sandbox)"""

    name: str
    """
    Custom sandbox name (auto-generated as sandbox-{user_id}-{timestamp} if not
    provided)
    """

    resources: Resources

    wait_for_ready: bool
    """Wait for sandbox to be ready before returning"""


class Resources(TypedDict, total=False):
    cpus: int
    """Number of CPUs (minimum: 1, 1 CPU = 0.25 Kubernetes vCPU)"""

    memory: int
    """Memory size in MiB"""

    storage: int
    """Storage size in GB"""

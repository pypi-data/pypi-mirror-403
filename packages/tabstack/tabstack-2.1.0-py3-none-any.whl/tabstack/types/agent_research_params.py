# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AgentResearchParams"]


class AgentResearchParams(TypedDict, total=False):
    query: Required[str]
    """The research query or question to answer"""

    fetch_timeout: int
    """Timeout in seconds for fetching web pages"""

    mode: Literal["fast", "balanced"]
    """Research mode: fast (quick answers), balanced (standard research, default)"""

    nocache: bool
    """Skip cache and force fresh research"""

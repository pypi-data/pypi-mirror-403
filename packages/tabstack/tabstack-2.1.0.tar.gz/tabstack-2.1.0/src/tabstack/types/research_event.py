# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["ResearchEvent"]


class ResearchEvent(BaseModel):
    data: Optional[object] = None
    """Event payload data"""

    event: Optional[Literal["phase", "progress", "complete", "error"]] = None
    """The event type: phase, progress, complete, or error"""

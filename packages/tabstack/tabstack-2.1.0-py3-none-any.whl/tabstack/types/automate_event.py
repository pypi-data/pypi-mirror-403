# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["AutomateEvent"]


class AutomateEvent(BaseModel):
    data: Optional[object] = None
    """Event payload data"""

    event: Optional[str] = None
    """The event type (e.g., start, agent:processing, complete)"""

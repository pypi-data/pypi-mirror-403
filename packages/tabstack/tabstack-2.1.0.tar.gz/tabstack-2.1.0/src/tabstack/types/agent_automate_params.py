# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AgentAutomateParams", "GeoTarget"]


class AgentAutomateParams(TypedDict, total=False):
    task: Required[str]
    """The task description in natural language"""

    data: object
    """JSON data to provide context for form filling or complex tasks"""

    geo_target: GeoTarget
    """Optional geotargeting parameters for proxy requests"""

    guardrails: str
    """Safety constraints for execution"""

    max_iterations: Annotated[int, PropertyInfo(alias="maxIterations")]
    """Maximum task iterations"""

    max_validation_attempts: Annotated[int, PropertyInfo(alias="maxValidationAttempts")]
    """Maximum validation attempts"""

    url: str
    """Starting URL for the task"""


class GeoTarget(TypedDict, total=False):
    """Optional geotargeting parameters for proxy requests"""

    country: str
    """
    Country code using ISO 3166-1 alpha-2 standard (2 letters, e.g., "US", "GB",
    "JP"). See: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    """

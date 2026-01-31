# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ExtractJsonParams", "GeoTarget"]


class ExtractJsonParams(TypedDict, total=False):
    json_schema: Required[object]
    """JSON schema definition that describes the structure of data to extract."""

    url: Required[str]
    """URL to fetch and extract data from"""

    geo_target: GeoTarget
    """Optional geotargeting parameters for proxy requests"""

    nocache: bool
    """Bypass cache and force fresh data retrieval"""


class GeoTarget(TypedDict, total=False):
    """Optional geotargeting parameters for proxy requests"""

    country: str
    """
    Country code using ISO 3166-1 alpha-2 standard (2 letters, e.g., "US", "GB",
    "JP"). See: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    """

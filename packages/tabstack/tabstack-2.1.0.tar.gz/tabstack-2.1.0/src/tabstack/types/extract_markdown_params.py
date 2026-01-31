# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ExtractMarkdownParams", "GeoTarget"]


class ExtractMarkdownParams(TypedDict, total=False):
    url: Required[str]
    """URL to fetch and convert to markdown"""

    geo_target: GeoTarget
    """Optional geotargeting parameters for proxy requests"""

    metadata: bool
    """
    Include extracted metadata (Open Graph and HTML metadata) as a separate field in
    the response
    """

    nocache: bool
    """Bypass cache and force fresh data retrieval"""


class GeoTarget(TypedDict, total=False):
    """Optional geotargeting parameters for proxy requests"""

    country: str
    """
    Country code using ISO 3166-1 alpha-2 standard (2 letters, e.g., "US", "GB",
    "JP"). See: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    """

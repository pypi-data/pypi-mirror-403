# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel

__all__ = ["ExtractMarkdownResponse", "Metadata"]


class Metadata(BaseModel):
    """
    Extracted metadata from the page (only included when metadata parameter is true)
    """

    author: Optional[str] = None
    """Author information from HTML metadata"""

    created_at: Optional[str] = None
    """Document creation date (ISO 8601)"""

    creator: Optional[str] = None
    """Creator application (e.g., "Microsoft Word")"""

    description: Optional[str] = None
    """Page description from Open Graph or HTML"""

    image: Optional[str] = None
    """Featured image URL from Open Graph"""

    keywords: Optional[List[str]] = None
    """PDF keywords as array"""

    modified_at: Optional[str] = None
    """Document modification date (ISO 8601)"""

    page_count: Optional[int] = None
    """Number of pages (PDF documents)"""

    pdf_version: Optional[str] = None
    """PDF version (e.g., "1.5")"""

    producer: Optional[str] = None
    """PDF producer software (e.g., "Adobe PDF Library")"""

    publisher: Optional[str] = None
    """Publisher information from Open Graph"""

    site_name: Optional[str] = None
    """Site name from Open Graph"""

    subject: Optional[str] = None
    """
    PDF-specific metadata fields (populated for PDF documents) PDF subject or
    summary
    """

    title: Optional[str] = None
    """Page title from Open Graph or HTML"""

    type: Optional[str] = None
    """Content type from Open Graph (e.g., article, website)"""

    url: Optional[str] = None
    """Canonical URL from Open Graph"""


class ExtractMarkdownResponse(BaseModel):
    content: str
    """The markdown content (includes metadata as YAML frontmatter by default)"""

    url: str
    """The URL that was converted to markdown"""

    metadata: Optional[Metadata] = None
    """
    Extracted metadata from the page (only included when metadata parameter is true)
    """

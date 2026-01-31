# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["StructuredSheetListParams"]


class StructuredSheetListParams(TypedDict, total=False):
    after: Optional[str]
    """Unique identifier for a structured sheet conversion."""

    limit: int
    """Maximum number of results to return per page."""

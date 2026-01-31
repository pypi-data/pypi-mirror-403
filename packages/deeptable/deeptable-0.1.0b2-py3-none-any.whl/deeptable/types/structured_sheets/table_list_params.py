# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["TableListParams"]


class TableListParams(TypedDict, total=False):
    after: Optional[str]
    """Unique identifier for a table."""

    limit: int
    """Maximum number of tables to return per page."""

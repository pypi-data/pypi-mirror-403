# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["StructuredSheetCreateParams"]


class StructuredSheetCreateParams(TypedDict, total=False):
    file_id: Required[str]
    """The unique identifier of the file to convert."""

    sheet_names: Optional[SequenceNotStr[str]]
    """List of sheet names to convert. If None, all sheets will be converted."""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["StructuredSheetResponse", "LastError"]


class LastError(BaseModel):
    """Error information when processing fails."""

    code: str
    """A machine-readable error code."""

    message: str
    """A human-readable description of the error."""


class StructuredSheetResponse(BaseModel):
    """Response representing a structured sheet conversion job.

    This is returned from POST (create), GET (retrieve), and list endpoints.
    """

    id: str
    """The unique identifier for this structured sheet conversion."""

    created_at: datetime
    """The timestamp when the conversion was started."""

    file_id: str
    """The unique identifier for the source file."""

    status: Literal["queued", "in_progress", "completed", "failed", "cancelled"]
    """The current processing status."""

    updated_at: datetime
    """The timestamp when the conversion was last updated."""

    last_error: Optional[LastError] = None
    """Error information when processing fails."""

    object: Optional[Literal["structured_sheet"]] = None
    """The object type, which is always 'structured_sheet'."""

    sheet_names: Optional[List[str]] = None
    """List of sheet names included in this conversion."""

    table_count: Optional[int] = None
    """Number of tables extracted from the workbook.

    Only present when status is 'completed'.
    """

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["TableResponse"]


class TableResponse(BaseModel):
    """Response representing a table extracted from a structured sheet.

    This is returned from GET (retrieve) and list table endpoints.
    Table names use a composite format: {normalized_sheet_name}__{table_name}.
    """

    id: str
    """The unique identifier for this table."""

    created_at: datetime
    """The timestamp when this table was created."""

    name: str
    """Composite table name: {normalized_sheet_name}\\__\\__{table_name}.

    Uses lowercase snake_case. Aggregation tables end with '**aggregations'.
    Example: 'staffing**head_count' or 'staffing**head_count**aggregations'.
    """

    sheet_name: str
    """The original Excel sheet name this table came from."""

    structured_sheet_id: str
    """The ID of the structured sheet this table belongs to."""

    type: Literal["relational", "aggregation", "tableless", "metadata"]
    """The type of table (relational, aggregation, or tableless)."""

    object: Optional[Literal["table"]] = None
    """The object type, which is always 'table'."""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["File"]


class File(BaseModel):
    """Response representing an uploaded file.

    This is returned from POST (upload), GET (retrieve), and list endpoints.
    """

    id: str
    """The unique identifier for this file."""

    content_type: str
    """The MIME type of the file."""

    created_at: datetime
    """The timestamp when the file was uploaded."""

    file_name: str
    """The original filename of the uploaded file."""

    size: int
    """The size of the file in bytes."""

    object: Optional[Literal["file"]] = None
    """The object type, which is always 'file'."""

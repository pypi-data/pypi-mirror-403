# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["TableDownloadParams"]


class TableDownloadParams(TypedDict, total=False):
    structured_sheet_id: Required[str]
    """The unique identifier of the structured sheet conversion."""

    format: Required[Literal["parquet", "csv"]]
    """The format to download the table data in."""

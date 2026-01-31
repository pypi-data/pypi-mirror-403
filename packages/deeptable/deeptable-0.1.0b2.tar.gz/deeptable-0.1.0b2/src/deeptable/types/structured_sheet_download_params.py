# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["StructuredSheetDownloadParams"]


class StructuredSheetDownloadParams(TypedDict, total=False):
    format: Literal["sqlite", "cell_labels"]
    """The export format to download."""

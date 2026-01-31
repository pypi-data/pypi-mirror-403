# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from .tables import (
    TablesResource,
    AsyncTablesResource,
    TablesResourceWithRawResponse,
    AsyncTablesResourceWithRawResponse,
    TablesResourceWithStreamingResponse,
    AsyncTablesResourceWithStreamingResponse,
)
from ...types import structured_sheet_list_params, structured_sheet_create_params, structured_sheet_download_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    to_custom_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_custom_streamed_response_wrapper,
    async_to_custom_raw_response_wrapper,
    async_to_custom_streamed_response_wrapper,
)
from ...pagination import SyncCursorIDPage, AsyncCursorIDPage
from ..._base_client import AsyncPaginator, make_request_options
from ...types.structured_sheet_response import StructuredSheetResponse
from ...types.structured_sheet_delete_response import StructuredSheetDeleteResponse

__all__ = ["StructuredSheetsResource", "AsyncStructuredSheetsResource"]


class StructuredSheetsResource(SyncAPIResource):
    @cached_property
    def tables(self) -> TablesResource:
        return TablesResource(self._client)

    @cached_property
    def with_raw_response(self) -> StructuredSheetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/deeptable-com/deeptable-python#accessing-raw-response-data-eg-headers
        """
        return StructuredSheetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StructuredSheetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/deeptable-com/deeptable-python#with_streaming_response
        """
        return StructuredSheetsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        file_id: str,
        sheet_names: Optional[SequenceNotStr[str]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetResponse:
        """Start converting a spreadsheet workbook into structured data.

        This initiates an
        asynchronous conversion process. Poll the returned resource using the `id` to
        check completion status.

        Args:
          file_id: The unique identifier of the file to convert.

          sheet_names: List of sheet names to convert. If None, all sheets will be converted.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/structured-sheets",
            body=maybe_transform(
                {
                    "file_id": file_id,
                    "sheet_names": sheet_names,
                },
                structured_sheet_create_params.StructuredSheetCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetResponse,
        )

    def retrieve(
        self,
        structured_sheet_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetResponse:
        """
        Get the status and details of a structured sheet conversion.

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        return self._get(
            f"/v1/structured-sheets/{structured_sheet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetResponse,
        )

    def list(
        self,
        *,
        after: Optional[str] | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorIDPage[StructuredSheetResponse]:
        """List all structured sheets conversions for the authenticated user.

        Results are
        paginated using cursor-based pagination.

        Args:
          after: Unique identifier for a structured sheet conversion.

          limit: Maximum number of results to return per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v1/structured-sheets",
            page=SyncCursorIDPage[StructuredSheetResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                    },
                    structured_sheet_list_params.StructuredSheetListParams,
                ),
            ),
            model=StructuredSheetResponse,
        )

    def delete(
        self,
        structured_sheet_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetDeleteResponse:
        """Delete a structured sheet conversion and its associated exports.

        This action
        cannot be undone.

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        return self._delete(
            f"/v1/structured-sheets/{structured_sheet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetDeleteResponse,
        )

    def cancel(
        self,
        structured_sheet_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetResponse:
        """Cancel a structured sheet conversion that is in progress.

        Only jobs with status
        'queued' or 'in_progress' can be cancelled.

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        return self._post(
            f"/v1/structured-sheets/{structured_sheet_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetResponse,
        )

    def download(
        self,
        structured_sheet_id: str,
        *,
        format: Literal["sqlite", "cell_labels"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BinaryAPIResponse:
        """Download the structured data in the specified format.

        Only available when
        conversion status is 'completed'.

        Available formats:

        - `sqlite`: SQLite database containing all extracted tables
        - `cell_labels`: CSV file with cell-level semantic labels

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          format: The export format to download.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        extra_headers = {"Accept": "application/x-sqlite3", **(extra_headers or {})}
        return self._get(
            f"/v1/structured-sheets/{structured_sheet_id}/download",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"format": format}, structured_sheet_download_params.StructuredSheetDownloadParams
                ),
            ),
            cast_to=BinaryAPIResponse,
        )


class AsyncStructuredSheetsResource(AsyncAPIResource):
    @cached_property
    def tables(self) -> AsyncTablesResource:
        return AsyncTablesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncStructuredSheetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/deeptable-com/deeptable-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStructuredSheetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStructuredSheetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/deeptable-com/deeptable-python#with_streaming_response
        """
        return AsyncStructuredSheetsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        file_id: str,
        sheet_names: Optional[SequenceNotStr[str]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetResponse:
        """Start converting a spreadsheet workbook into structured data.

        This initiates an
        asynchronous conversion process. Poll the returned resource using the `id` to
        check completion status.

        Args:
          file_id: The unique identifier of the file to convert.

          sheet_names: List of sheet names to convert. If None, all sheets will be converted.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/structured-sheets",
            body=await async_maybe_transform(
                {
                    "file_id": file_id,
                    "sheet_names": sheet_names,
                },
                structured_sheet_create_params.StructuredSheetCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetResponse,
        )

    async def retrieve(
        self,
        structured_sheet_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetResponse:
        """
        Get the status and details of a structured sheet conversion.

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        return await self._get(
            f"/v1/structured-sheets/{structured_sheet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetResponse,
        )

    def list(
        self,
        *,
        after: Optional[str] | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[StructuredSheetResponse, AsyncCursorIDPage[StructuredSheetResponse]]:
        """List all structured sheets conversions for the authenticated user.

        Results are
        paginated using cursor-based pagination.

        Args:
          after: Unique identifier for a structured sheet conversion.

          limit: Maximum number of results to return per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/v1/structured-sheets",
            page=AsyncCursorIDPage[StructuredSheetResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                    },
                    structured_sheet_list_params.StructuredSheetListParams,
                ),
            ),
            model=StructuredSheetResponse,
        )

    async def delete(
        self,
        structured_sheet_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetDeleteResponse:
        """Delete a structured sheet conversion and its associated exports.

        This action
        cannot be undone.

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        return await self._delete(
            f"/v1/structured-sheets/{structured_sheet_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetDeleteResponse,
        )

    async def cancel(
        self,
        structured_sheet_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StructuredSheetResponse:
        """Cancel a structured sheet conversion that is in progress.

        Only jobs with status
        'queued' or 'in_progress' can be cancelled.

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        return await self._post(
            f"/v1/structured-sheets/{structured_sheet_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StructuredSheetResponse,
        )

    async def download(
        self,
        structured_sheet_id: str,
        *,
        format: Literal["sqlite", "cell_labels"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncBinaryAPIResponse:
        """Download the structured data in the specified format.

        Only available when
        conversion status is 'completed'.

        Available formats:

        - `sqlite`: SQLite database containing all extracted tables
        - `cell_labels`: CSV file with cell-level semantic labels

        Args:
          structured_sheet_id: The unique identifier of the structured sheet conversion.

          format: The export format to download.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not structured_sheet_id:
            raise ValueError(
                f"Expected a non-empty value for `structured_sheet_id` but received {structured_sheet_id!r}"
            )
        extra_headers = {"Accept": "application/x-sqlite3", **(extra_headers or {})}
        return await self._get(
            f"/v1/structured-sheets/{structured_sheet_id}/download",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"format": format}, structured_sheet_download_params.StructuredSheetDownloadParams
                ),
            ),
            cast_to=AsyncBinaryAPIResponse,
        )


class StructuredSheetsResourceWithRawResponse:
    def __init__(self, structured_sheets: StructuredSheetsResource) -> None:
        self._structured_sheets = structured_sheets

        self.create = to_raw_response_wrapper(
            structured_sheets.create,
        )
        self.retrieve = to_raw_response_wrapper(
            structured_sheets.retrieve,
        )
        self.list = to_raw_response_wrapper(
            structured_sheets.list,
        )
        self.delete = to_raw_response_wrapper(
            structured_sheets.delete,
        )
        self.cancel = to_raw_response_wrapper(
            structured_sheets.cancel,
        )
        self.download = to_custom_raw_response_wrapper(
            structured_sheets.download,
            BinaryAPIResponse,
        )

    @cached_property
    def tables(self) -> TablesResourceWithRawResponse:
        return TablesResourceWithRawResponse(self._structured_sheets.tables)


class AsyncStructuredSheetsResourceWithRawResponse:
    def __init__(self, structured_sheets: AsyncStructuredSheetsResource) -> None:
        self._structured_sheets = structured_sheets

        self.create = async_to_raw_response_wrapper(
            structured_sheets.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            structured_sheets.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            structured_sheets.list,
        )
        self.delete = async_to_raw_response_wrapper(
            structured_sheets.delete,
        )
        self.cancel = async_to_raw_response_wrapper(
            structured_sheets.cancel,
        )
        self.download = async_to_custom_raw_response_wrapper(
            structured_sheets.download,
            AsyncBinaryAPIResponse,
        )

    @cached_property
    def tables(self) -> AsyncTablesResourceWithRawResponse:
        return AsyncTablesResourceWithRawResponse(self._structured_sheets.tables)


class StructuredSheetsResourceWithStreamingResponse:
    def __init__(self, structured_sheets: StructuredSheetsResource) -> None:
        self._structured_sheets = structured_sheets

        self.create = to_streamed_response_wrapper(
            structured_sheets.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            structured_sheets.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            structured_sheets.list,
        )
        self.delete = to_streamed_response_wrapper(
            structured_sheets.delete,
        )
        self.cancel = to_streamed_response_wrapper(
            structured_sheets.cancel,
        )
        self.download = to_custom_streamed_response_wrapper(
            structured_sheets.download,
            StreamedBinaryAPIResponse,
        )

    @cached_property
    def tables(self) -> TablesResourceWithStreamingResponse:
        return TablesResourceWithStreamingResponse(self._structured_sheets.tables)


class AsyncStructuredSheetsResourceWithStreamingResponse:
    def __init__(self, structured_sheets: AsyncStructuredSheetsResource) -> None:
        self._structured_sheets = structured_sheets

        self.create = async_to_streamed_response_wrapper(
            structured_sheets.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            structured_sheets.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            structured_sheets.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            structured_sheets.delete,
        )
        self.cancel = async_to_streamed_response_wrapper(
            structured_sheets.cancel,
        )
        self.download = async_to_custom_streamed_response_wrapper(
            structured_sheets.download,
            AsyncStreamedBinaryAPIResponse,
        )

    @cached_property
    def tables(self) -> AsyncTablesResourceWithStreamingResponse:
        return AsyncTablesResourceWithStreamingResponse(self._structured_sheets.tables)

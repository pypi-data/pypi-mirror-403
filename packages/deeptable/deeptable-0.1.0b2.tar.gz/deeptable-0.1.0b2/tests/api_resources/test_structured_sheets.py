# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from deeptable import DeepTable, AsyncDeepTable
from tests.utils import assert_matches_type
from deeptable.types import (
    StructuredSheetResponse,
    StructuredSheetDeleteResponse,
)
from deeptable._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)
from deeptable.pagination import SyncCursorIDPage, AsyncCursorIDPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStructuredSheets:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
            sheet_names=["Sheet1", "Financials"],
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: DeepTable) -> None:
        response = client.structured_sheets.with_raw_response.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = response.parse()
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: DeepTable) -> None:
        with client.structured_sheets.with_streaming_response.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = response.parse()
            assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.retrieve(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: DeepTable) -> None:
        response = client.structured_sheets.with_raw_response.retrieve(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = response.parse()
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: DeepTable) -> None:
        with client.structured_sheets.with_streaming_response.retrieve(
            "ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = response.parse()
            assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.list()
        assert_matches_type(SyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.list(
            after="ss_01kfxgjd94fn9stqm42nejb627",
            limit=20,
        )
        assert_matches_type(SyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: DeepTable) -> None:
        response = client.structured_sheets.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = response.parse()
        assert_matches_type(SyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: DeepTable) -> None:
        with client.structured_sheets.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = response.parse()
            assert_matches_type(SyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.delete(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(StructuredSheetDeleteResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: DeepTable) -> None:
        response = client.structured_sheets.with_raw_response.delete(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = response.parse()
        assert_matches_type(StructuredSheetDeleteResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: DeepTable) -> None:
        with client.structured_sheets.with_streaming_response.delete(
            "ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = response.parse()
            assert_matches_type(StructuredSheetDeleteResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: DeepTable) -> None:
        structured_sheet = client.structured_sheets.cancel(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: DeepTable) -> None:
        response = client.structured_sheets.with_raw_response.cancel(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = response.parse()
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: DeepTable) -> None:
        with client.structured_sheets.with_streaming_response.cancel(
            "ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = response.parse()
            assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.with_raw_response.cancel(
                "",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_download(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        structured_sheet = client.structured_sheets.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert structured_sheet.is_closed
        assert structured_sheet.json() == {"foo": "bar"}
        assert cast(Any, structured_sheet.is_closed) is True
        assert isinstance(structured_sheet, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_download_with_all_params(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        structured_sheet = client.structured_sheets.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="sqlite",
        )
        assert structured_sheet.is_closed
        assert structured_sheet.json() == {"foo": "bar"}
        assert cast(Any, structured_sheet.is_closed) is True
        assert isinstance(structured_sheet, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_download(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        structured_sheet = client.structured_sheets.with_raw_response.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert structured_sheet.is_closed is True
        assert structured_sheet.http_request.headers.get("X-Stainless-Lang") == "python"
        assert structured_sheet.json() == {"foo": "bar"}
        assert isinstance(structured_sheet, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_download(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        with client.structured_sheets.with_streaming_response.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        ) as structured_sheet:
            assert not structured_sheet.is_closed
            assert structured_sheet.http_request.headers.get("X-Stainless-Lang") == "python"

            assert structured_sheet.json() == {"foo": "bar"}
            assert cast(Any, structured_sheet.is_closed) is True
            assert isinstance(structured_sheet, StreamedBinaryAPIResponse)

        assert cast(Any, structured_sheet.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_download(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.with_raw_response.download(
                structured_sheet_id="",
            )


class TestAsyncStructuredSheets:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
            sheet_names=["Sheet1", "Financials"],
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.with_raw_response.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = await response.parse()
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.with_streaming_response.create(
            file_id="file_01h45ytscbebyvny4gc8cr8ma2",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = await response.parse()
            assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.retrieve(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.with_raw_response.retrieve(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = await response.parse()
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.with_streaming_response.retrieve(
            "ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = await response.parse()
            assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.list()
        assert_matches_type(AsyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.list(
            after="ss_01kfxgjd94fn9stqm42nejb627",
            limit=20,
        )
        assert_matches_type(AsyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = await response.parse()
        assert_matches_type(AsyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = await response.parse()
            assert_matches_type(AsyncCursorIDPage[StructuredSheetResponse], structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.delete(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(StructuredSheetDeleteResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.with_raw_response.delete(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = await response.parse()
        assert_matches_type(StructuredSheetDeleteResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.with_streaming_response.delete(
            "ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = await response.parse()
            assert_matches_type(StructuredSheetDeleteResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncDeepTable) -> None:
        structured_sheet = await async_client.structured_sheets.cancel(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.with_raw_response.cancel(
            "ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        structured_sheet = await response.parse()
        assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.with_streaming_response.cancel(
            "ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            structured_sheet = await response.parse()
            assert_matches_type(StructuredSheetResponse, structured_sheet, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.with_raw_response.cancel(
                "",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_download(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        structured_sheet = await async_client.structured_sheets.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert structured_sheet.is_closed
        assert await structured_sheet.json() == {"foo": "bar"}
        assert cast(Any, structured_sheet.is_closed) is True
        assert isinstance(structured_sheet, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_download_with_all_params(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        structured_sheet = await async_client.structured_sheets.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="sqlite",
        )
        assert structured_sheet.is_closed
        assert await structured_sheet.json() == {"foo": "bar"}
        assert cast(Any, structured_sheet.is_closed) is True
        assert isinstance(structured_sheet, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_download(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )

        structured_sheet = await async_client.structured_sheets.with_raw_response.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert structured_sheet.is_closed is True
        assert structured_sheet.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await structured_sheet.json() == {"foo": "bar"}
        assert isinstance(structured_sheet, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_download(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/download").mock(
            return_value=httpx.Response(200, json={"foo": "bar"})
        )
        async with async_client.structured_sheets.with_streaming_response.download(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        ) as structured_sheet:
            assert not structured_sheet.is_closed
            assert structured_sheet.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await structured_sheet.json() == {"foo": "bar"}
            assert cast(Any, structured_sheet.is_closed) is True
            assert isinstance(structured_sheet, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, structured_sheet.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_download(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.with_raw_response.download(
                structured_sheet_id="",
            )

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from deeptable import DeepTable, AsyncDeepTable
from tests.utils import assert_matches_type
from deeptable._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)
from deeptable.pagination import SyncCursorIDPage, AsyncCursorIDPage
from deeptable.types.structured_sheets import TableResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTables:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: DeepTable) -> None:
        table = client.structured_sheets.tables.retrieve(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(TableResponse, table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: DeepTable) -> None:
        response = client.structured_sheets.tables.with_raw_response.retrieve(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        table = response.parse()
        assert_matches_type(TableResponse, table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: DeepTable) -> None:
        with client.structured_sheets.tables.with_streaming_response.retrieve(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            table = response.parse()
            assert_matches_type(TableResponse, table, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.tables.with_raw_response.retrieve(
                table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
                structured_sheet_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `table_id` but received ''"):
            client.structured_sheets.tables.with_raw_response.retrieve(
                table_id="",
                structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: DeepTable) -> None:
        table = client.structured_sheets.tables.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(SyncCursorIDPage[TableResponse], table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: DeepTable) -> None:
        table = client.structured_sheets.tables.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            after="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            limit=20,
        )
        assert_matches_type(SyncCursorIDPage[TableResponse], table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: DeepTable) -> None:
        response = client.structured_sheets.tables.with_raw_response.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        table = response.parse()
        assert_matches_type(SyncCursorIDPage[TableResponse], table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: DeepTable) -> None:
        with client.structured_sheets.tables.with_streaming_response.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            table = response.parse()
            assert_matches_type(SyncCursorIDPage[TableResponse], table, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.tables.with_raw_response.list(
                structured_sheet_id="",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_download(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get(
            "/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/tables/tbl_01kfxgjd94fn9stqm45rqr2pnz/download"
        ).mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        table = client.structured_sheets.tables.download(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="parquet",
        )
        assert table.is_closed
        assert table.json() == {"foo": "bar"}
        assert cast(Any, table.is_closed) is True
        assert isinstance(table, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_download(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get(
            "/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/tables/tbl_01kfxgjd94fn9stqm45rqr2pnz/download"
        ).mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        table = client.structured_sheets.tables.with_raw_response.download(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="parquet",
        )

        assert table.is_closed is True
        assert table.http_request.headers.get("X-Stainless-Lang") == "python"
        assert table.json() == {"foo": "bar"}
        assert isinstance(table, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_download(self, client: DeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get(
            "/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/tables/tbl_01kfxgjd94fn9stqm45rqr2pnz/download"
        ).mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.structured_sheets.tables.with_streaming_response.download(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="parquet",
        ) as table:
            assert not table.is_closed
            assert table.http_request.headers.get("X-Stainless-Lang") == "python"

            assert table.json() == {"foo": "bar"}
            assert cast(Any, table.is_closed) is True
            assert isinstance(table, StreamedBinaryAPIResponse)

        assert cast(Any, table.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_download(self, client: DeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            client.structured_sheets.tables.with_raw_response.download(
                table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
                structured_sheet_id="",
                format="parquet",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `table_id` but received ''"):
            client.structured_sheets.tables.with_raw_response.download(
                table_id="",
                structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
                format="parquet",
            )


class TestAsyncTables:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncDeepTable) -> None:
        table = await async_client.structured_sheets.tables.retrieve(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(TableResponse, table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.tables.with_raw_response.retrieve(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        table = await response.parse()
        assert_matches_type(TableResponse, table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.tables.with_streaming_response.retrieve(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            table = await response.parse()
            assert_matches_type(TableResponse, table, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.tables.with_raw_response.retrieve(
                table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
                structured_sheet_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `table_id` but received ''"):
            await async_client.structured_sheets.tables.with_raw_response.retrieve(
                table_id="",
                structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncDeepTable) -> None:
        table = await async_client.structured_sheets.tables.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )
        assert_matches_type(AsyncCursorIDPage[TableResponse], table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncDeepTable) -> None:
        table = await async_client.structured_sheets.tables.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            after="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            limit=20,
        )
        assert_matches_type(AsyncCursorIDPage[TableResponse], table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncDeepTable) -> None:
        response = await async_client.structured_sheets.tables.with_raw_response.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        table = await response.parse()
        assert_matches_type(AsyncCursorIDPage[TableResponse], table, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncDeepTable) -> None:
        async with async_client.structured_sheets.tables.with_streaming_response.list(
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            table = await response.parse()
            assert_matches_type(AsyncCursorIDPage[TableResponse], table, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.tables.with_raw_response.list(
                structured_sheet_id="",
            )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_download(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get(
            "/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/tables/tbl_01kfxgjd94fn9stqm45rqr2pnz/download"
        ).mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        table = await async_client.structured_sheets.tables.download(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="parquet",
        )
        assert table.is_closed
        assert await table.json() == {"foo": "bar"}
        assert cast(Any, table.is_closed) is True
        assert isinstance(table, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_download(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get(
            "/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/tables/tbl_01kfxgjd94fn9stqm45rqr2pnz/download"
        ).mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        table = await async_client.structured_sheets.tables.with_raw_response.download(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="parquet",
        )

        assert table.is_closed is True
        assert table.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await table.json() == {"foo": "bar"}
        assert isinstance(table, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_download(self, async_client: AsyncDeepTable, respx_mock: MockRouter) -> None:
        respx_mock.get(
            "/v1/structured-sheets/ss_01kfxgjd94fn9stqm42nejb627/tables/tbl_01kfxgjd94fn9stqm45rqr2pnz/download"
        ).mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.structured_sheets.tables.with_streaming_response.download(
            table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
            structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
            format="parquet",
        ) as table:
            assert not table.is_closed
            assert table.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await table.json() == {"foo": "bar"}
            assert cast(Any, table.is_closed) is True
            assert isinstance(table, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, table.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_download(self, async_client: AsyncDeepTable) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `structured_sheet_id` but received ''"):
            await async_client.structured_sheets.tables.with_raw_response.download(
                table_id="tbl_01kfxgjd94fn9stqm45rqr2pnz",
                structured_sheet_id="",
                format="parquet",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `table_id` but received ''"):
            await async_client.structured_sheets.tables.with_raw_response.download(
                table_id="",
                structured_sheet_id="ss_01kfxgjd94fn9stqm42nejb627",
                format="parquet",
            )

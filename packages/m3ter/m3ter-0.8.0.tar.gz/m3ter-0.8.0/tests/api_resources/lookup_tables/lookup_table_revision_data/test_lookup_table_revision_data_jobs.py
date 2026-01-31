# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.lookup_tables.lookup_table_revision_data import (
    LookupTableRevisionDataJobListResponse,
    LookupTableRevisionDataJobDeleteResponse,
    LookupTableRevisionDataJobDownloadResponse,
    LookupTableRevisionDataJobRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLookupTableRevisionDataJobs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        lookup_table_revision_data_job = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.retrieve(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )
        )
        assert_matches_type(
            LookupTableRevisionDataJobRetrieveResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = response.parse()
        assert_matches_type(
            LookupTableRevisionDataJobRetrieveResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = response.parse()
            assert_matches_type(
                LookupTableRevisionDataJobRetrieveResponse, lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="id",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        lookup_table_revision_data_job = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
            )
        )
        assert_matches_type(
            SyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data_job = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
                next_token="nextToken",
                page_size=1,
            )
        )
        assert_matches_type(
            SyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
            )
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = response.parse()
        assert_matches_type(
            SyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.list(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = response.parse()
            assert_matches_type(
                SyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.list(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        lookup_table_revision_data_job = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.delete(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )
        )
        assert_matches_type(LookupTableRevisionDataJobDeleteResponse, lookup_table_revision_data_job, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = response.parse()
        assert_matches_type(LookupTableRevisionDataJobDeleteResponse, lookup_table_revision_data_job, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = response.parse()
            assert_matches_type(
                LookupTableRevisionDataJobDeleteResponse, lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="id",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    def test_method_download(self, client: M3ter) -> None:
        lookup_table_revision_data_job = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.download(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )
        )
        assert_matches_type(
            LookupTableRevisionDataJobDownloadResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_raw_response_download(self, client: M3ter) -> None:
        response = (
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.download(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = response.parse()
        assert_matches_type(
            LookupTableRevisionDataJobDownloadResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    def test_streaming_response_download(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.download(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = response.parse()
            assert_matches_type(
                LookupTableRevisionDataJobDownloadResponse, lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_download(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.download(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                content_type="application/jsonl",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.download(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )


class TestAsyncLookupTableRevisionDataJobs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data_job = (
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.retrieve(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )
        )
        assert_matches_type(
            LookupTableRevisionDataJobRetrieveResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = await response.parse()
        assert_matches_type(
            LookupTableRevisionDataJobRetrieveResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = await response.parse()
            assert_matches_type(
                LookupTableRevisionDataJobRetrieveResponse, lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="id",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.retrieve(
                id="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data_job = (
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
            )
        )
        assert_matches_type(
            AsyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data_job = (
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
                next_token="nextToken",
                page_size=1,
            )
        )
        assert_matches_type(
            AsyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.list(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = await response.parse()
        assert_matches_type(
            AsyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.list(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = await response.parse()
            assert_matches_type(
                AsyncCursor[LookupTableRevisionDataJobListResponse], lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.list(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.list(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data_job = (
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.delete(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )
        )
        assert_matches_type(LookupTableRevisionDataJobDeleteResponse, lookup_table_revision_data_job, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = await response.parse()
        assert_matches_type(LookupTableRevisionDataJobDeleteResponse, lookup_table_revision_data_job, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = await response.parse()
            assert_matches_type(
                LookupTableRevisionDataJobDeleteResponse, lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="id",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="id",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.delete(
                id="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    async def test_method_download(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data_job = (
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.download(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )
        )
        assert_matches_type(
            LookupTableRevisionDataJobDownloadResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_raw_response_download(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.download(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data_job = await response.parse()
        assert_matches_type(
            LookupTableRevisionDataJobDownloadResponse, lookup_table_revision_data_job, path=["response"]
        )

    @parametrize
    async def test_streaming_response_download(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_streaming_response.download(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data_job = await response.parse()
            assert_matches_type(
                LookupTableRevisionDataJobDownloadResponse, lookup_table_revision_data_job, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_download(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.download(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                content_type="application/jsonl",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_jobs.with_raw_response.download(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )

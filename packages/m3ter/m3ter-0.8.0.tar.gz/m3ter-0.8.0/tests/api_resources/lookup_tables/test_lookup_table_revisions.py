# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.lookup_tables import (
    LookupTableRevisionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLookupTableRevisions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.create(
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.create(
            lookup_table_id="lookupTableId",
            fields=[
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
            ],
            keys=["foo", "bar", "baz"],
            name="x",
            custom_fields={"foo": "string"},
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            version=0,
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revisions.with_raw_response.create(
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revisions.with_streaming_response.create(
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.create(
                lookup_table_id="",
                fields=[{"type": "STRING"}, {"type": "STRING"}],
                keys=["foo", "bar", "baz"],
                name="x",
            )

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revisions.with_raw_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revisions.with_streaming_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.retrieve(
                id="id",
                lookup_table_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.retrieve(
                id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
            ],
            keys=["foo", "bar", "baz"],
            name="x",
            custom_fields={"foo": "string"},
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            version=0,
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revisions.with_raw_response.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revisions.with_streaming_response.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.update(
                id="id",
                lookup_table_id="",
                fields=[{"type": "STRING"}, {"type": "STRING"}],
                keys=["foo", "bar", "baz"],
                name="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.update(
                id="",
                lookup_table_id="lookupTableId",
                fields=[{"type": "STRING"}, {"type": "STRING"}],
                keys=["foo", "bar", "baz"],
                name="x",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.list(
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(SyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.list(
            lookup_table_id="lookupTableId",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revisions.with_raw_response.list(
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = response.parse()
        assert_matches_type(SyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revisions.with_streaming_response.list(
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = response.parse()
            assert_matches_type(SyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.list(
                lookup_table_id="",
            )

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.delete(
            id="id",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revisions.with_raw_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revisions.with_streaming_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.delete(
                id="id",
                lookup_table_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.delete(
                id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    def test_method_update_status(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.update_status(
            id="id",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_method_update_status_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision = client.lookup_tables.lookup_table_revisions.update_status(
            id="id",
            lookup_table_id="lookupTableId",
            status="DRAFT",
            version=0,
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_raw_response_update_status(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revisions.with_raw_response.update_status(
            id="id",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    def test_streaming_response_update_status(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revisions.with_streaming_response.update_status(
            id="id",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_status(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.update_status(
                id="id",
                lookup_table_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.lookup_tables.lookup_table_revisions.with_raw_response.update_status(
                id="",
                lookup_table_id="lookupTableId",
            )


class TestAsyncLookupTableRevisions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.create(
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.create(
            lookup_table_id="lookupTableId",
            fields=[
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
            ],
            keys=["foo", "bar", "baz"],
            name="x",
            custom_fields={"foo": "string"},
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            version=0,
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revisions.with_raw_response.create(
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = await response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revisions.with_streaming_response.create(
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = await response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.create(
                lookup_table_id="",
                fields=[{"type": "STRING"}, {"type": "STRING"}],
                keys=["foo", "bar", "baz"],
                name="x",
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revisions.with_raw_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = await response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revisions.with_streaming_response.retrieve(
            id="id",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = await response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.retrieve(
                id="id",
                lookup_table_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.retrieve(
                id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
                {
                    "type": "STRING",
                    "name": "lookupfield",
                },
            ],
            keys=["foo", "bar", "baz"],
            name="x",
            custom_fields={"foo": "string"},
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            version=0,
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revisions.with_raw_response.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = await response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revisions.with_streaming_response.update(
            id="id",
            lookup_table_id="lookupTableId",
            fields=[{"type": "STRING"}, {"type": "STRING"}],
            keys=["foo", "bar", "baz"],
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = await response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.update(
                id="id",
                lookup_table_id="",
                fields=[{"type": "STRING"}, {"type": "STRING"}],
                keys=["foo", "bar", "baz"],
                name="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.update(
                id="",
                lookup_table_id="lookupTableId",
                fields=[{"type": "STRING"}, {"type": "STRING"}],
                keys=["foo", "bar", "baz"],
                name="x",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.list(
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(AsyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.list(
            lookup_table_id="lookupTableId",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revisions.with_raw_response.list(
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = await response.parse()
        assert_matches_type(AsyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revisions.with_streaming_response.list(
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = await response.parse()
            assert_matches_type(AsyncCursor[LookupTableRevisionResponse], lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.list(
                lookup_table_id="",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.delete(
            id="id",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revisions.with_raw_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = await response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revisions.with_streaming_response.delete(
            id="id",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = await response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.delete(
                id="id",
                lookup_table_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.delete(
                id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    async def test_method_update_status(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.update_status(
            id="id",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_method_update_status_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision = await async_client.lookup_tables.lookup_table_revisions.update_status(
            id="id",
            lookup_table_id="lookupTableId",
            status="DRAFT",
            version=0,
        )
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_raw_response_update_status(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revisions.with_raw_response.update_status(
            id="id",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision = await response.parse()
        assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

    @parametrize
    async def test_streaming_response_update_status(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revisions.with_streaming_response.update_status(
            id="id",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision = await response.parse()
            assert_matches_type(LookupTableRevisionResponse, lookup_table_revision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_status(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.update_status(
                id="id",
                lookup_table_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.lookup_tables.lookup_table_revisions.with_raw_response.update_status(
                id="",
                lookup_table_id="lookupTableId",
            )

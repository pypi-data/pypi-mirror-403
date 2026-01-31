# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.types.lookup_tables import (
    LookupTableRevisionDataCopyResponse,
    LookupTableRevisionDataDeleteResponse,
    LookupTableRevisionDataUpdateResponse,
    LookupTableRevisionDataArchieveResponse,
    LookupTableRevisionDataRetrieveResponse,
    LookupTableRevisionDataDeleteKeyResponse,
    LookupTableRevisionDataUpdateKeyResponse,
    LookupTableRevisionDataRetrieveKeyResponse,
    LookupTableRevisionDataGenerateDownloadURLResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLookupTableRevisionData:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_method_retrieve_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            additional=["string"],
            limit=0,
        )
        assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
        )
        assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
            additional=["string"],
            version=0,
        )
        assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.update(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                items=[{"foo": "bar"}],
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.update(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                items=[{"foo": "bar"}],
            )

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.delete(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionDataDeleteResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.delete(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataDeleteResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.delete(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataDeleteResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.delete(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.delete(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    def test_method_archieve(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.archieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        )
        assert_matches_type(LookupTableRevisionDataArchieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_archieve(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.archieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataArchieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_archieve(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.archieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataArchieveResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_archieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.archieve(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                content_type="application/jsonl",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.archieve(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )

    @parametrize
    def test_method_copy(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_method_copy_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            revision_id="revisionId",
        )
        assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_copy(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_copy(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_copy(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.copy(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.copy(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    def test_method_delete_key(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )
        assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_method_delete_key_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            version=0,
        )
        assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_delete_key(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_delete_key(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete_key(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
                lookup_key="lookupKey",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
                lookup_key="lookupKey",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_key` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
                lookup_key="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    def test_method_generate_download_url(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
        )
        assert_matches_type(
            LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
        )

    @parametrize
    def test_method_generate_download_url_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
            version=0,
        )
        assert_matches_type(
            LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
        )

    @parametrize
    def test_raw_response_generate_download_url(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(
            LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
        )

    @parametrize
    def test_streaming_response_generate_download_url(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(
                LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_generate_download_url(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.generate_download_url(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                content_length=1,
                content_type="application/jsonl",
                file_name="x",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.generate_download_url(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                content_length=1,
                content_type="application/jsonl",
                file_name="x",
            )

    @parametrize
    def test_method_retrieve_key(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.retrieve_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )
        assert_matches_type(LookupTableRevisionDataRetrieveKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_retrieve_key(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataRetrieveKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_retrieve_key(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.retrieve_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(
                LookupTableRevisionDataRetrieveKeyResponse, lookup_table_revision_data, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve_key(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
                lookup_key="lookupKey",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
                lookup_key="lookupKey",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_key` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
                lookup_key="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    def test_method_update_key(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
        )
        assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_method_update_key_with_all_params(self, client: M3ter) -> None:
        lookup_table_revision_data = client.lookup_tables.lookup_table_revision_data.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
            additional=["string"],
            version=0,
        )
        assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_raw_response_update_key(self, client: M3ter) -> None:
        response = client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = response.parse()
        assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    def test_streaming_response_update_key(self, client: M3ter) -> None:
        with client.lookup_tables.lookup_table_revision_data.with_streaming_response.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = response.parse()
            assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_key(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
                lookup_key="lookupKey",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
                item={"foo": "bar"},
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
                lookup_key="lookupKey",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
                item={"foo": "bar"},
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_key` but received ''"):
            client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
                lookup_key="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
                item={"foo": "bar"},
            )


class TestAsyncLookupTableRevisionData:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            additional=["string"],
            limit=0,
        )
        assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.retrieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataRetrieveResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
        )
        assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
            additional=["string"],
            version=0,
        )
        assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.update(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            items=[{"foo": "bar"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataUpdateResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                items=[{"foo": "bar"}],
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                items=[{"foo": "bar"}],
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.delete(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionDataDeleteResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataDeleteResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.delete(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataDeleteResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    async def test_method_archieve(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.archieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        )
        assert_matches_type(LookupTableRevisionDataArchieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_archieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.archieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataArchieveResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_archieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.archieve(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_type="application/jsonl",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataArchieveResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_archieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.archieve(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                content_type="application/jsonl",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.archieve(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                content_type="application/jsonl",
            )

    @parametrize
    async def test_method_copy(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )
        assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_method_copy_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            revision_id="revisionId",
        )
        assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_copy(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_copy(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.copy(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataCopyResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_copy(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.copy(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.copy(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
            )

    @parametrize
    async def test_method_delete_key(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )
        assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_method_delete_key_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            version=0,
        )
        assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_delete_key(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_delete_key(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.delete_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataDeleteKeyResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete_key(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
                lookup_key="lookupKey",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
                lookup_key="lookupKey",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_key` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.delete_key(
                lookup_key="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    async def test_method_generate_download_url(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
        )
        assert_matches_type(
            LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
        )

    @parametrize
    async def test_method_generate_download_url_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
            version=0,
        )
        assert_matches_type(
            LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
        )

    @parametrize
    async def test_raw_response_generate_download_url(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(
            LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
        )

    @parametrize
    async def test_streaming_response_generate_download_url(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.generate_download_url(
            lookup_table_revision_id="lookupTableRevisionId",
            lookup_table_id="lookupTableId",
            content_length=1,
            content_type="application/jsonl",
            file_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(
                LookupTableRevisionDataGenerateDownloadURLResponse, lookup_table_revision_data, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_generate_download_url(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.generate_download_url(
                lookup_table_revision_id="lookupTableRevisionId",
                lookup_table_id="",
                content_length=1,
                content_type="application/jsonl",
                file_name="x",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.generate_download_url(
                lookup_table_revision_id="",
                lookup_table_id="lookupTableId",
                content_length=1,
                content_type="application/jsonl",
                file_name="x",
            )

    @parametrize
    async def test_method_retrieve_key(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.retrieve_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )
        assert_matches_type(LookupTableRevisionDataRetrieveKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_retrieve_key(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataRetrieveKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve_key(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.retrieve_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(
                LookupTableRevisionDataRetrieveKeyResponse, lookup_table_revision_data, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve_key(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
                lookup_key="lookupKey",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
                lookup_key="lookupKey",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_key` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.retrieve_key(
                lookup_key="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
            )

    @parametrize
    async def test_method_update_key(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
        )
        assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_method_update_key_with_all_params(self, async_client: AsyncM3ter) -> None:
        lookup_table_revision_data = await async_client.lookup_tables.lookup_table_revision_data.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
            additional=["string"],
            version=0,
        )
        assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_raw_response_update_key(self, async_client: AsyncM3ter) -> None:
        response = await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        lookup_table_revision_data = await response.parse()
        assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

    @parametrize
    async def test_streaming_response_update_key(self, async_client: AsyncM3ter) -> None:
        async with async_client.lookup_tables.lookup_table_revision_data.with_streaming_response.update_key(
            lookup_key="lookupKey",
            lookup_table_id="lookupTableId",
            lookup_table_revision_id="lookupTableRevisionId",
            item={"foo": "bar"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            lookup_table_revision_data = await response.parse()
            assert_matches_type(LookupTableRevisionDataUpdateKeyResponse, lookup_table_revision_data, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_key(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_table_id` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
                lookup_key="lookupKey",
                lookup_table_id="",
                lookup_table_revision_id="lookupTableRevisionId",
                item={"foo": "bar"},
            )

        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `lookup_table_revision_id` but received ''"
        ):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
                lookup_key="lookupKey",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="",
                item={"foo": "bar"},
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `lookup_key` but received ''"):
            await async_client.lookup_tables.lookup_table_revision_data.with_raw_response.update_key(
                lookup_key="",
                lookup_table_id="lookupTableId",
                lookup_table_revision_id="lookupTableRevisionId",
                item={"foo": "bar"},
            )

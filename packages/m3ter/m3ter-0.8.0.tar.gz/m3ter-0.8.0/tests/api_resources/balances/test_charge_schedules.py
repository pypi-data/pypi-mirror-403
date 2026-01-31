# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter._utils import parse_date, parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.balances import (
    ChargeScheduleListResponse,
    ChargeScheduleCreateResponse,
    ChargeScheduleDeleteResponse,
    ChargeScheduleUpdateResponse,
    ChargeSchedulePreviewResponse,
    ChargeScheduleRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestChargeSchedules:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            amount=0,
            bill_epoch=parse_date("2019-12-27"),
            custom_fields={"foo": "string"},
            unit_price=0,
            units=0,
            version=0,
        )
        assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.balances.charge_schedules.with_raw_response.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = response.parse()
        assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.balances.charge_schedules.with_streaming_response.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = response.parse()
            assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.charge_schedules.with_raw_response.create(
                balance_id="",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.retrieve(
            id="id",
            balance_id="balanceId",
        )
        assert_matches_type(ChargeScheduleRetrieveResponse, charge_schedule, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.balances.charge_schedules.with_raw_response.retrieve(
            id="id",
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = response.parse()
        assert_matches_type(ChargeScheduleRetrieveResponse, charge_schedule, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.balances.charge_schedules.with_streaming_response.retrieve(
            id="id",
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = response.parse()
            assert_matches_type(ChargeScheduleRetrieveResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.charge_schedules.with_raw_response.retrieve(
                id="id",
                balance_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.balances.charge_schedules.with_raw_response.retrieve(
                id="",
                balance_id="balanceId",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            amount=0,
            bill_epoch=parse_date("2019-12-27"),
            custom_fields={"foo": "string"},
            unit_price=0,
            units=0,
            version=0,
        )
        assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.balances.charge_schedules.with_raw_response.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = response.parse()
        assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.balances.charge_schedules.with_streaming_response.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = response.parse()
            assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.charge_schedules.with_raw_response.update(
                id="id",
                balance_id="",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.balances.charge_schedules.with_raw_response.update(
                id="",
                balance_id="balanceId",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.list(
            balance_id="balanceId",
        )
        assert_matches_type(SyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.list(
            balance_id="balanceId",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.balances.charge_schedules.with_raw_response.list(
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = response.parse()
        assert_matches_type(SyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.balances.charge_schedules.with_streaming_response.list(
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = response.parse()
            assert_matches_type(SyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.charge_schedules.with_raw_response.list(
                balance_id="",
            )

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.delete(
            id="id",
            balance_id="balanceId",
        )
        assert_matches_type(ChargeScheduleDeleteResponse, charge_schedule, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.balances.charge_schedules.with_raw_response.delete(
            id="id",
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = response.parse()
        assert_matches_type(ChargeScheduleDeleteResponse, charge_schedule, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.balances.charge_schedules.with_streaming_response.delete(
            id="id",
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = response.parse()
            assert_matches_type(ChargeScheduleDeleteResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.charge_schedules.with_raw_response.delete(
                id="id",
                balance_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.balances.charge_schedules.with_raw_response.delete(
                id="",
                balance_id="balanceId",
            )

    @parametrize
    def test_method_preview(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

    @parametrize
    def test_method_preview_with_all_params(self, client: M3ter) -> None:
        charge_schedule = client.balances.charge_schedules.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            next_token="nextToken",
            page_size=1,
            amount=0,
            bill_epoch=parse_date("2019-12-27"),
            custom_fields={"foo": "string"},
            unit_price=0,
            units=0,
            version=0,
        )
        assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

    @parametrize
    def test_raw_response_preview(self, client: M3ter) -> None:
        response = client.balances.charge_schedules.with_raw_response.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = response.parse()
        assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

    @parametrize
    def test_streaming_response_preview(self, client: M3ter) -> None:
        with client.balances.charge_schedules.with_streaming_response.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = response.parse()
            assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_preview(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.charge_schedules.with_raw_response.preview(
                balance_id="",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )


class TestAsyncChargeSchedules:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            amount=0,
            bill_epoch=parse_date("2019-12-27"),
            custom_fields={"foo": "string"},
            unit_price=0,
            units=0,
            version=0,
        )
        assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.charge_schedules.with_raw_response.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = await response.parse()
        assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.charge_schedules.with_streaming_response.create(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = await response.parse()
            assert_matches_type(ChargeScheduleCreateResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.create(
                balance_id="",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.retrieve(
            id="id",
            balance_id="balanceId",
        )
        assert_matches_type(ChargeScheduleRetrieveResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.charge_schedules.with_raw_response.retrieve(
            id="id",
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = await response.parse()
        assert_matches_type(ChargeScheduleRetrieveResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.charge_schedules.with_streaming_response.retrieve(
            id="id",
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = await response.parse()
            assert_matches_type(ChargeScheduleRetrieveResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.retrieve(
                id="id",
                balance_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.retrieve(
                id="",
                balance_id="balanceId",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            amount=0,
            bill_epoch=parse_date("2019-12-27"),
            custom_fields={"foo": "string"},
            unit_price=0,
            units=0,
            version=0,
        )
        assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.charge_schedules.with_raw_response.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = await response.parse()
        assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.charge_schedules.with_streaming_response.update(
            id="id",
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = await response.parse()
            assert_matches_type(ChargeScheduleUpdateResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.update(
                id="id",
                balance_id="",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.update(
                id="",
                balance_id="balanceId",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.list(
            balance_id="balanceId",
        )
        assert_matches_type(AsyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.list(
            balance_id="balanceId",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.charge_schedules.with_raw_response.list(
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = await response.parse()
        assert_matches_type(AsyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.charge_schedules.with_streaming_response.list(
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = await response.parse()
            assert_matches_type(AsyncCursor[ChargeScheduleListResponse], charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.list(
                balance_id="",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.delete(
            id="id",
            balance_id="balanceId",
        )
        assert_matches_type(ChargeScheduleDeleteResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.charge_schedules.with_raw_response.delete(
            id="id",
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = await response.parse()
        assert_matches_type(ChargeScheduleDeleteResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.charge_schedules.with_streaming_response.delete(
            id="id",
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = await response.parse()
            assert_matches_type(ChargeScheduleDeleteResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.delete(
                id="id",
                balance_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.delete(
                id="",
                balance_id="balanceId",
            )

    @parametrize
    async def test_method_preview(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_method_preview_with_all_params(self, async_client: AsyncM3ter) -> None:
        charge_schedule = await async_client.balances.charge_schedules.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            next_token="nextToken",
            page_size=1,
            amount=0,
            bill_epoch=parse_date("2019-12-27"),
            custom_fields={"foo": "string"},
            unit_price=0,
            units=0,
            version=0,
        )
        assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_raw_response_preview(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.charge_schedules.with_raw_response.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        charge_schedule = await response.parse()
        assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

    @parametrize
    async def test_streaming_response_preview(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.charge_schedules.with_streaming_response.preview(
            balance_id="balanceId",
            bill_frequency="DAILY",
            bill_frequency_interval=1,
            bill_in_advance=True,
            charge_description="x",
            code='S?oC"$]C] ]]]]]5]',
            currency="currency",
            name="x",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            charge_schedule = await response.parse()
            assert_matches_type(ChargeSchedulePreviewResponse, charge_schedule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_preview(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.charge_schedules.with_raw_response.preview(
                balance_id="",
                bill_frequency="DAILY",
                bill_frequency_interval=1,
                bill_in_advance=True,
                charge_description="x",
                code='S?oC"$]C] ]]]]]5]',
                currency="currency",
                name="x",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

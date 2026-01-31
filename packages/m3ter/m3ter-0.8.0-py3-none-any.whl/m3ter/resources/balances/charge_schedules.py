# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from datetime import date, datetime
from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursor, AsyncCursor
from ..._base_client import AsyncPaginator, make_request_options
from ...types.balances import (
    charge_schedule_list_params,
    charge_schedule_create_params,
    charge_schedule_update_params,
    charge_schedule_preview_params,
)
from ...types.balances.charge_schedule_list_response import ChargeScheduleListResponse
from ...types.balances.charge_schedule_create_response import ChargeScheduleCreateResponse
from ...types.balances.charge_schedule_delete_response import ChargeScheduleDeleteResponse
from ...types.balances.charge_schedule_update_response import ChargeScheduleUpdateResponse
from ...types.balances.charge_schedule_preview_response import ChargeSchedulePreviewResponse
from ...types.balances.charge_schedule_retrieve_response import ChargeScheduleRetrieveResponse

__all__ = ["ChargeSchedulesResource", "AsyncChargeSchedulesResource"]


class ChargeSchedulesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ChargeSchedulesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ChargeSchedulesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChargeSchedulesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return ChargeSchedulesResourceWithStreamingResponse(self)

    def create(
        self,
        balance_id: str,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        bill_frequency_interval: int,
        bill_in_advance: bool,
        charge_description: str,
        code: str,
        currency: str,
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        amount: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleCreateResponse:
        """
        Create a new BalanceChargeSchedule.

        Args:
          bill_frequency: Represents standard scheduling frequencies options for a job.

          bill_frequency_interval: How often Bills are issued. For example, if billFrequency is `MONTHLY` and
              `billFrequencyInterval` is 3, Bills are issued every three months.

          bill_in_advance: Used to specify how Charges created by the Balance Charge Schedule are billed -
              either in arrears or in advance:

              - Use `false` for billing in arrears.
              - Use `true` for billing in advance.

          charge_description: The description for Charges created by the Balance Charge Schedule. Used on
              Bills for Charge line items.

          code: Unique short code for the Balance Charge Schedule.

          currency: The currency of the Charges created by the Balance Charge Schedule.

          name: The name of the Balance Charge Schedule.

          service_period_end_date: The service period end date (_in ISO-8601 format_) of the Balance Charge
              Schedule.

          service_period_start_date: The service period start date (_in ISO-8601 format)_ of the Balance Charge
              Schedule.

          amount: The amount of each Charge created by the Balance Charge Schedule. Must be
              omitted if `units` and `unitPrice` are provided.

          bill_epoch: Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
              created for Balance Charges created by the Schedule, and also acts as a
              reference for when in the Schedule period subsequent Bills are created for the
              defined `billFrequency`. If left blank, then the relevant Epoch date from your
              Organization's configuration will be used as the billing cycle date instead.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          unit_price: Unit price for Charge. Must be provided when `units` is used. Must be omitted
              when `amount` is used.

          units: Number of units defined for the Charges created by the Schedule. Required when
              `unitPrice` is provided. Must be omitted when `amount` is used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        return self._post(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules",
            body=maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "bill_frequency_interval": bill_frequency_interval,
                    "bill_in_advance": bill_in_advance,
                    "charge_description": charge_description,
                    "code": code,
                    "currency": currency,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "amount": amount,
                    "bill_epoch": bill_epoch,
                    "custom_fields": custom_fields,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_schedule_create_params.ChargeScheduleCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleCreateResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        balance_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleRetrieveResponse:
        """
        Retrieve a BalanceChargeSchedule for the given UUID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        balance_id: str,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        bill_frequency_interval: int,
        bill_in_advance: bool,
        charge_description: str,
        code: str,
        currency: str,
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        amount: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleUpdateResponse:
        """
        Update a BalanceChargeSchedule for the given UUID.

        Args:
          bill_frequency: Represents standard scheduling frequencies options for a job.

          bill_frequency_interval: How often Bills are issued. For example, if billFrequency is `MONTHLY` and
              `billFrequencyInterval` is 3, Bills are issued every three months.

          bill_in_advance: Used to specify how Charges created by the Balance Charge Schedule are billed -
              either in arrears or in advance:

              - Use `false` for billing in arrears.
              - Use `true` for billing in advance.

          charge_description: The description for Charges created by the Balance Charge Schedule. Used on
              Bills for Charge line items.

          code: Unique short code for the Balance Charge Schedule.

          currency: The currency of the Charges created by the Balance Charge Schedule.

          name: The name of the Balance Charge Schedule.

          service_period_end_date: The service period end date (_in ISO-8601 format_) of the Balance Charge
              Schedule.

          service_period_start_date: The service period start date (_in ISO-8601 format)_ of the Balance Charge
              Schedule.

          amount: The amount of each Charge created by the Balance Charge Schedule. Must be
              omitted if `units` and `unitPrice` are provided.

          bill_epoch: Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
              created for Balance Charges created by the Schedule, and also acts as a
              reference for when in the Schedule period subsequent Bills are created for the
              defined `billFrequency`. If left blank, then the relevant Epoch date from your
              Organization's configuration will be used as the billing cycle date instead.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          unit_price: Unit price for Charge. Must be provided when `units` is used. Must be omitted
              when `amount` is used.

          units: Number of units defined for the Charges created by the Schedule. Required when
              `unitPrice` is provided. Must be omitted when `amount` is used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/{id}",
            body=maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "bill_frequency_interval": bill_frequency_interval,
                    "bill_in_advance": bill_in_advance,
                    "charge_description": charge_description,
                    "code": code,
                    "currency": currency,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "amount": amount,
                    "bill_epoch": bill_epoch,
                    "custom_fields": custom_fields,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_schedule_update_params.ChargeScheduleUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleUpdateResponse,
        )

    def list(
        self,
        balance_id: str,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ChargeScheduleListResponse]:
        """
        Retrieve a list of BalanceChargeSchedule entities

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of BalanceChargeSchedules to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules",
            page=SyncCursor[ChargeScheduleListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    charge_schedule_list_params.ChargeScheduleListParams,
                ),
            ),
            model=ChargeScheduleListResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        balance_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleDeleteResponse:
        """
        Delete the BalanceChargeSchedule for the given UUID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleDeleteResponse,
        )

    def preview(
        self,
        balance_id: str,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        bill_frequency_interval: int,
        bill_in_advance: bool,
        charge_description: str,
        code: str,
        currency: str,
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        amount: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeSchedulePreviewResponse:
        """Previews the Charges this Schedule would create, without persisting them.

        You
        can use this call to obtain a preview of the Charges a Schedule you plan to
        create for a Balance would generate.

        Args:
          bill_frequency: Represents standard scheduling frequencies options for a job.

          bill_frequency_interval: How often Bills are issued. For example, if billFrequency is `MONTHLY` and
              `billFrequencyInterval` is 3, Bills are issued every three months.

          bill_in_advance: Used to specify how Charges created by the Balance Charge Schedule are billed -
              either in arrears or in advance:

              - Use `false` for billing in arrears.
              - Use `true` for billing in advance.

          charge_description: The description for Charges created by the Balance Charge Schedule. Used on
              Bills for Charge line items.

          code: Unique short code for the Balance Charge Schedule.

          currency: The currency of the Charges created by the Balance Charge Schedule.

          name: The name of the Balance Charge Schedule.

          service_period_end_date: The service period end date (_in ISO-8601 format_) of the Balance Charge
              Schedule.

          service_period_start_date: The service period start date (_in ISO-8601 format)_ of the Balance Charge
              Schedule.

          next_token: nextToken for multi page retrievals

          page_size: Number of Charges to retrieve per page

          amount: The amount of each Charge created by the Balance Charge Schedule. Must be
              omitted if `units` and `unitPrice` are provided.

          bill_epoch: Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
              created for Balance Charges created by the Schedule, and also acts as a
              reference for when in the Schedule period subsequent Bills are created for the
              defined `billFrequency`. If left blank, then the relevant Epoch date from your
              Organization's configuration will be used as the billing cycle date instead.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          unit_price: Unit price for Charge. Must be provided when `units` is used. Must be omitted
              when `amount` is used.

          units: Number of units defined for the Charges created by the Schedule. Required when
              `unitPrice` is provided. Must be omitted when `amount` is used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        return self._post(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/preview",
            body=maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "bill_frequency_interval": bill_frequency_interval,
                    "bill_in_advance": bill_in_advance,
                    "charge_description": charge_description,
                    "code": code,
                    "currency": currency,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "amount": amount,
                    "bill_epoch": bill_epoch,
                    "custom_fields": custom_fields,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_schedule_preview_params.ChargeSchedulePreviewParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    charge_schedule_preview_params.ChargeSchedulePreviewParams,
                ),
            ),
            cast_to=ChargeSchedulePreviewResponse,
        )


class AsyncChargeSchedulesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncChargeSchedulesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncChargeSchedulesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChargeSchedulesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncChargeSchedulesResourceWithStreamingResponse(self)

    async def create(
        self,
        balance_id: str,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        bill_frequency_interval: int,
        bill_in_advance: bool,
        charge_description: str,
        code: str,
        currency: str,
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        amount: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleCreateResponse:
        """
        Create a new BalanceChargeSchedule.

        Args:
          bill_frequency: Represents standard scheduling frequencies options for a job.

          bill_frequency_interval: How often Bills are issued. For example, if billFrequency is `MONTHLY` and
              `billFrequencyInterval` is 3, Bills are issued every three months.

          bill_in_advance: Used to specify how Charges created by the Balance Charge Schedule are billed -
              either in arrears or in advance:

              - Use `false` for billing in arrears.
              - Use `true` for billing in advance.

          charge_description: The description for Charges created by the Balance Charge Schedule. Used on
              Bills for Charge line items.

          code: Unique short code for the Balance Charge Schedule.

          currency: The currency of the Charges created by the Balance Charge Schedule.

          name: The name of the Balance Charge Schedule.

          service_period_end_date: The service period end date (_in ISO-8601 format_) of the Balance Charge
              Schedule.

          service_period_start_date: The service period start date (_in ISO-8601 format)_ of the Balance Charge
              Schedule.

          amount: The amount of each Charge created by the Balance Charge Schedule. Must be
              omitted if `units` and `unitPrice` are provided.

          bill_epoch: Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
              created for Balance Charges created by the Schedule, and also acts as a
              reference for when in the Schedule period subsequent Bills are created for the
              defined `billFrequency`. If left blank, then the relevant Epoch date from your
              Organization's configuration will be used as the billing cycle date instead.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          unit_price: Unit price for Charge. Must be provided when `units` is used. Must be omitted
              when `amount` is used.

          units: Number of units defined for the Charges created by the Schedule. Required when
              `unitPrice` is provided. Must be omitted when `amount` is used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        return await self._post(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules",
            body=await async_maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "bill_frequency_interval": bill_frequency_interval,
                    "bill_in_advance": bill_in_advance,
                    "charge_description": charge_description,
                    "code": code,
                    "currency": currency,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "amount": amount,
                    "bill_epoch": bill_epoch,
                    "custom_fields": custom_fields,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_schedule_create_params.ChargeScheduleCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleCreateResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        balance_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleRetrieveResponse:
        """
        Retrieve a BalanceChargeSchedule for the given UUID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        balance_id: str,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        bill_frequency_interval: int,
        bill_in_advance: bool,
        charge_description: str,
        code: str,
        currency: str,
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        amount: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleUpdateResponse:
        """
        Update a BalanceChargeSchedule for the given UUID.

        Args:
          bill_frequency: Represents standard scheduling frequencies options for a job.

          bill_frequency_interval: How often Bills are issued. For example, if billFrequency is `MONTHLY` and
              `billFrequencyInterval` is 3, Bills are issued every three months.

          bill_in_advance: Used to specify how Charges created by the Balance Charge Schedule are billed -
              either in arrears or in advance:

              - Use `false` for billing in arrears.
              - Use `true` for billing in advance.

          charge_description: The description for Charges created by the Balance Charge Schedule. Used on
              Bills for Charge line items.

          code: Unique short code for the Balance Charge Schedule.

          currency: The currency of the Charges created by the Balance Charge Schedule.

          name: The name of the Balance Charge Schedule.

          service_period_end_date: The service period end date (_in ISO-8601 format_) of the Balance Charge
              Schedule.

          service_period_start_date: The service period start date (_in ISO-8601 format)_ of the Balance Charge
              Schedule.

          amount: The amount of each Charge created by the Balance Charge Schedule. Must be
              omitted if `units` and `unitPrice` are provided.

          bill_epoch: Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
              created for Balance Charges created by the Schedule, and also acts as a
              reference for when in the Schedule period subsequent Bills are created for the
              defined `billFrequency`. If left blank, then the relevant Epoch date from your
              Organization's configuration will be used as the billing cycle date instead.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          unit_price: Unit price for Charge. Must be provided when `units` is used. Must be omitted
              when `amount` is used.

          units: Number of units defined for the Charges created by the Schedule. Required when
              `unitPrice` is provided. Must be omitted when `amount` is used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/{id}",
            body=await async_maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "bill_frequency_interval": bill_frequency_interval,
                    "bill_in_advance": bill_in_advance,
                    "charge_description": charge_description,
                    "code": code,
                    "currency": currency,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "amount": amount,
                    "bill_epoch": bill_epoch,
                    "custom_fields": custom_fields,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_schedule_update_params.ChargeScheduleUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleUpdateResponse,
        )

    def list(
        self,
        balance_id: str,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ChargeScheduleListResponse, AsyncCursor[ChargeScheduleListResponse]]:
        """
        Retrieve a list of BalanceChargeSchedule entities

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of BalanceChargeSchedules to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules",
            page=AsyncCursor[ChargeScheduleListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    charge_schedule_list_params.ChargeScheduleListParams,
                ),
            ),
            model=ChargeScheduleListResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        balance_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeScheduleDeleteResponse:
        """
        Delete the BalanceChargeSchedule for the given UUID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeScheduleDeleteResponse,
        )

    async def preview(
        self,
        balance_id: str,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        bill_frequency_interval: int,
        bill_in_advance: bool,
        charge_description: str,
        code: str,
        currency: str,
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        amount: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeSchedulePreviewResponse:
        """Previews the Charges this Schedule would create, without persisting them.

        You
        can use this call to obtain a preview of the Charges a Schedule you plan to
        create for a Balance would generate.

        Args:
          bill_frequency: Represents standard scheduling frequencies options for a job.

          bill_frequency_interval: How often Bills are issued. For example, if billFrequency is `MONTHLY` and
              `billFrequencyInterval` is 3, Bills are issued every three months.

          bill_in_advance: Used to specify how Charges created by the Balance Charge Schedule are billed -
              either in arrears or in advance:

              - Use `false` for billing in arrears.
              - Use `true` for billing in advance.

          charge_description: The description for Charges created by the Balance Charge Schedule. Used on
              Bills for Charge line items.

          code: Unique short code for the Balance Charge Schedule.

          currency: The currency of the Charges created by the Balance Charge Schedule.

          name: The name of the Balance Charge Schedule.

          service_period_end_date: The service period end date (_in ISO-8601 format_) of the Balance Charge
              Schedule.

          service_period_start_date: The service period start date (_in ISO-8601 format)_ of the Balance Charge
              Schedule.

          next_token: nextToken for multi page retrievals

          page_size: Number of Charges to retrieve per page

          amount: The amount of each Charge created by the Balance Charge Schedule. Must be
              omitted if `units` and `unitPrice` are provided.

          bill_epoch: Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
              created for Balance Charges created by the Schedule, and also acts as a
              reference for when in the Schedule period subsequent Bills are created for the
              defined `billFrequency`. If left blank, then the relevant Epoch date from your
              Organization's configuration will be used as the billing cycle date instead.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          unit_price: Unit price for Charge. Must be provided when `units` is used. Must be omitted
              when `amount` is used.

          units: Number of units defined for the Charges created by the Schedule. Required when
              `unitPrice` is provided. Must be omitted when `amount` is used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not balance_id:
            raise ValueError(f"Expected a non-empty value for `balance_id` but received {balance_id!r}")
        return await self._post(
            f"/organizations/{org_id}/balances/{balance_id}/balancechargeschedules/preview",
            body=await async_maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "bill_frequency_interval": bill_frequency_interval,
                    "bill_in_advance": bill_in_advance,
                    "charge_description": charge_description,
                    "code": code,
                    "currency": currency,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "amount": amount,
                    "bill_epoch": bill_epoch,
                    "custom_fields": custom_fields,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_schedule_preview_params.ChargeSchedulePreviewParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    charge_schedule_preview_params.ChargeSchedulePreviewParams,
                ),
            ),
            cast_to=ChargeSchedulePreviewResponse,
        )


class ChargeSchedulesResourceWithRawResponse:
    def __init__(self, charge_schedules: ChargeSchedulesResource) -> None:
        self._charge_schedules = charge_schedules

        self.create = to_raw_response_wrapper(
            charge_schedules.create,
        )
        self.retrieve = to_raw_response_wrapper(
            charge_schedules.retrieve,
        )
        self.update = to_raw_response_wrapper(
            charge_schedules.update,
        )
        self.list = to_raw_response_wrapper(
            charge_schedules.list,
        )
        self.delete = to_raw_response_wrapper(
            charge_schedules.delete,
        )
        self.preview = to_raw_response_wrapper(
            charge_schedules.preview,
        )


class AsyncChargeSchedulesResourceWithRawResponse:
    def __init__(self, charge_schedules: AsyncChargeSchedulesResource) -> None:
        self._charge_schedules = charge_schedules

        self.create = async_to_raw_response_wrapper(
            charge_schedules.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            charge_schedules.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            charge_schedules.update,
        )
        self.list = async_to_raw_response_wrapper(
            charge_schedules.list,
        )
        self.delete = async_to_raw_response_wrapper(
            charge_schedules.delete,
        )
        self.preview = async_to_raw_response_wrapper(
            charge_schedules.preview,
        )


class ChargeSchedulesResourceWithStreamingResponse:
    def __init__(self, charge_schedules: ChargeSchedulesResource) -> None:
        self._charge_schedules = charge_schedules

        self.create = to_streamed_response_wrapper(
            charge_schedules.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            charge_schedules.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            charge_schedules.update,
        )
        self.list = to_streamed_response_wrapper(
            charge_schedules.list,
        )
        self.delete = to_streamed_response_wrapper(
            charge_schedules.delete,
        )
        self.preview = to_streamed_response_wrapper(
            charge_schedules.preview,
        )


class AsyncChargeSchedulesResourceWithStreamingResponse:
    def __init__(self, charge_schedules: AsyncChargeSchedulesResource) -> None:
        self._charge_schedules = charge_schedules

        self.create = async_to_streamed_response_wrapper(
            charge_schedules.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            charge_schedules.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            charge_schedules.update,
        )
        self.list = async_to_streamed_response_wrapper(
            charge_schedules.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            charge_schedules.delete,
        )
        self.preview = async_to_streamed_response_wrapper(
            charge_schedules.preview,
        )

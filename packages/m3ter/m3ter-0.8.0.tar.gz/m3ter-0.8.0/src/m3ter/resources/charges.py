# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date, datetime
from typing_extensions import Literal

import httpx

from ..types import charge_list_params, charge_create_params, charge_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursor, AsyncCursor
from .._base_client import AsyncPaginator, make_request_options
from ..types.charge_list_response import ChargeListResponse
from ..types.charge_create_response import ChargeCreateResponse
from ..types.charge_delete_response import ChargeDeleteResponse
from ..types.charge_update_response import ChargeUpdateResponse
from ..types.charge_retrieve_response import ChargeRetrieveResponse

__all__ = ["ChargesResource", "AsyncChargesResource"]


class ChargesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ChargesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ChargesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChargesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return ChargesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        code: str,
        currency: str,
        entity_type: Literal["AD_HOC", "BALANCE"],
        line_item_type: Literal["BALANCE_FEE", "AD_HOC"],
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        amount: float | Omit = omit,
        bill_date: str | Omit = omit,
        contract_id: str | Omit = omit,
        description: str | Omit = omit,
        entity_id: str | Omit = omit,
        notes: str | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeCreateResponse:
        """
        Create a new Charge.

        **NOTES:**

        - To create an ad-hoc Charge on an Account, use the `accountId` request
          parameter.
        - To create a balance fee Charge for a Balance, use the `entityId` request
          parameter to specify which Balance on an Account the Charge is for.
        - To define the value of the Charge amount that is billed, you can simply
          specify an `amount` or use a number of `units` together with a `unitPrice` for
          a calculated value = units x unit price. But you cannot specify _both an
          amount and units/unit price_.

        Args:
          account_id: The ID of the Account the Charge is being created for.

          code: Unique short code for the Charge.

          currency: Charge currency.

          entity_type: The entity type the Charge has been created for.

          line_item_type: Available line item types that can be used for billing a Charge.

          name: Name of the Charge. Added to the Bill line item description for this Charge.

          service_period_end_date: The service period end date (_in ISO-8601 format_)for the Charge.

              **NOTE:** End date is exclusive.

          service_period_start_date: The service period start date (_in ISO-8601 format_) for the Charge.

          accounting_product_id: The Accounting Product ID assigned to the Charge.

          amount: Amount of the Charge. If `amount` is provided, then `units` and `unitPrice` must
              be omitted.

          bill_date: The date when the Charge will be added to a Bill.

          contract_id: The ID of a Contract on the Account that the Charge will be added to.

          description: The description added to the Bill line item for the Charge.

          entity_id: The ID of the Charge linked entity. For example, the ID of an Account Balance if
              a Balance Charge.

              **NOTE:** If `entityType` is `BALANCE`, you must provide the `entityId` of the
              Balance the Charge is for.

          notes: Used to enter information about the Charge for accounting purposes, such as the
              reason it was created. This information will not be added to a Bill line item
              for the Charge.

          unit_price: Unit price. If `amount` is omitted, then provide together with `units`. When
              `amount` is provided, `unitPrice` must be omitted.

          units: Number of units of the Charge. If `amount` is omitted, then provide together
              with `unitPrice`. When `amount` is provided, `units` must be omitted.

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
        return self._post(
            f"/organizations/{org_id}/charges",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "code": code,
                    "currency": currency,
                    "entity_type": entity_type,
                    "line_item_type": line_item_type,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "bill_date": bill_date,
                    "contract_id": contract_id,
                    "description": description,
                    "entity_id": entity_id,
                    "notes": notes,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_create_params.ChargeCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeCreateResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeRetrieveResponse:
        """
        Retrieve a Charge for the given UUID.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/charges/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        code: str,
        currency: str,
        entity_type: Literal["AD_HOC", "BALANCE"],
        line_item_type: Literal["BALANCE_FEE", "AD_HOC"],
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        amount: float | Omit = omit,
        bill_date: str | Omit = omit,
        contract_id: str | Omit = omit,
        description: str | Omit = omit,
        entity_id: str | Omit = omit,
        notes: str | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeUpdateResponse:
        """
        Update a Charge for the given UUID.

        **NOTE:** When you update a Charge on an Account, you can provide either a
        Charge `amount` or Charge `units` together with a `unitPrice`, but _not both_.

        Args:
          account_id: The ID of the Account the Charge is being created for.

          code: Unique short code for the Charge.

          currency: Charge currency.

          entity_type: The entity type the Charge has been created for.

          line_item_type: Available line item types that can be used for billing a Charge.

          name: Name of the Charge. Added to the Bill line item description for this Charge.

          service_period_end_date: The service period end date (_in ISO-8601 format_)for the Charge.

              **NOTE:** End date is exclusive.

          service_period_start_date: The service period start date (_in ISO-8601 format_) for the Charge.

          accounting_product_id: The Accounting Product ID assigned to the Charge.

          amount: Amount of the Charge. If `amount` is provided, then `units` and `unitPrice` must
              be omitted.

          bill_date: The date when the Charge will be added to a Bill.

          contract_id: The ID of a Contract on the Account that the Charge will be added to.

          description: The description added to the Bill line item for the Charge.

          entity_id: The ID of the Charge linked entity. For example, the ID of an Account Balance if
              a Balance Charge.

              **NOTE:** If `entityType` is `BALANCE`, you must provide the `entityId` of the
              Balance the Charge is for.

          notes: Used to enter information about the Charge for accounting purposes, such as the
              reason it was created. This information will not be added to a Bill line item
              for the Charge.

          unit_price: Unit price. If `amount` is omitted, then provide together with `units`. When
              `amount` is provided, `unitPrice` must be omitted.

          units: Number of units of the Charge. If `amount` is omitted, then provide together
              with `unitPrice`. When `amount` is provided, `units` must be omitted.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/charges/{id}",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "code": code,
                    "currency": currency,
                    "entity_type": entity_type,
                    "line_item_type": line_item_type,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "bill_date": bill_date,
                    "contract_id": contract_id,
                    "description": description,
                    "entity_id": entity_id,
                    "notes": notes,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_update_params.ChargeUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeUpdateResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        bill_date: Union[str, date] | Omit = omit,
        entity_id: str | Omit = omit,
        entity_type: Literal["AD_HOC", "BALANCE"] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        schedule_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ChargeListResponse]:
        """
        Retrieve a list of Charge entities

        Args:
          account_id: List Charge items for the Account UUID

          bill_date: List Charge items for the Bill Date

          entity_id: List Charge items for the Entity UUID

          entity_type: List Charge items for the EntityType

          ids: List of Charge UUIDs to retrieve

          next_token: nextToken for multi page retrievals

          page_size: Number of Charges to retrieve per page

          schedule_id: List Charge items for the Schedule UUID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/charges",
            page=SyncCursor[ChargeListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "bill_date": bill_date,
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "schedule_id": schedule_id,
                    },
                    charge_list_params.ChargeListParams,
                ),
            ),
            model=ChargeListResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeDeleteResponse:
        """
        Delete the Charge for the given UUID.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/charges/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeDeleteResponse,
        )


class AsyncChargesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncChargesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncChargesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChargesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncChargesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        code: str,
        currency: str,
        entity_type: Literal["AD_HOC", "BALANCE"],
        line_item_type: Literal["BALANCE_FEE", "AD_HOC"],
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        amount: float | Omit = omit,
        bill_date: str | Omit = omit,
        contract_id: str | Omit = omit,
        description: str | Omit = omit,
        entity_id: str | Omit = omit,
        notes: str | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeCreateResponse:
        """
        Create a new Charge.

        **NOTES:**

        - To create an ad-hoc Charge on an Account, use the `accountId` request
          parameter.
        - To create a balance fee Charge for a Balance, use the `entityId` request
          parameter to specify which Balance on an Account the Charge is for.
        - To define the value of the Charge amount that is billed, you can simply
          specify an `amount` or use a number of `units` together with a `unitPrice` for
          a calculated value = units x unit price. But you cannot specify _both an
          amount and units/unit price_.

        Args:
          account_id: The ID of the Account the Charge is being created for.

          code: Unique short code for the Charge.

          currency: Charge currency.

          entity_type: The entity type the Charge has been created for.

          line_item_type: Available line item types that can be used for billing a Charge.

          name: Name of the Charge. Added to the Bill line item description for this Charge.

          service_period_end_date: The service period end date (_in ISO-8601 format_)for the Charge.

              **NOTE:** End date is exclusive.

          service_period_start_date: The service period start date (_in ISO-8601 format_) for the Charge.

          accounting_product_id: The Accounting Product ID assigned to the Charge.

          amount: Amount of the Charge. If `amount` is provided, then `units` and `unitPrice` must
              be omitted.

          bill_date: The date when the Charge will be added to a Bill.

          contract_id: The ID of a Contract on the Account that the Charge will be added to.

          description: The description added to the Bill line item for the Charge.

          entity_id: The ID of the Charge linked entity. For example, the ID of an Account Balance if
              a Balance Charge.

              **NOTE:** If `entityType` is `BALANCE`, you must provide the `entityId` of the
              Balance the Charge is for.

          notes: Used to enter information about the Charge for accounting purposes, such as the
              reason it was created. This information will not be added to a Bill line item
              for the Charge.

          unit_price: Unit price. If `amount` is omitted, then provide together with `units`. When
              `amount` is provided, `unitPrice` must be omitted.

          units: Number of units of the Charge. If `amount` is omitted, then provide together
              with `unitPrice`. When `amount` is provided, `units` must be omitted.

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
        return await self._post(
            f"/organizations/{org_id}/charges",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "code": code,
                    "currency": currency,
                    "entity_type": entity_type,
                    "line_item_type": line_item_type,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "bill_date": bill_date,
                    "contract_id": contract_id,
                    "description": description,
                    "entity_id": entity_id,
                    "notes": notes,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_create_params.ChargeCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeCreateResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeRetrieveResponse:
        """
        Retrieve a Charge for the given UUID.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/charges/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        code: str,
        currency: str,
        entity_type: Literal["AD_HOC", "BALANCE"],
        line_item_type: Literal["BALANCE_FEE", "AD_HOC"],
        name: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        amount: float | Omit = omit,
        bill_date: str | Omit = omit,
        contract_id: str | Omit = omit,
        description: str | Omit = omit,
        entity_id: str | Omit = omit,
        notes: str | Omit = omit,
        unit_price: float | Omit = omit,
        units: float | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeUpdateResponse:
        """
        Update a Charge for the given UUID.

        **NOTE:** When you update a Charge on an Account, you can provide either a
        Charge `amount` or Charge `units` together with a `unitPrice`, but _not both_.

        Args:
          account_id: The ID of the Account the Charge is being created for.

          code: Unique short code for the Charge.

          currency: Charge currency.

          entity_type: The entity type the Charge has been created for.

          line_item_type: Available line item types that can be used for billing a Charge.

          name: Name of the Charge. Added to the Bill line item description for this Charge.

          service_period_end_date: The service period end date (_in ISO-8601 format_)for the Charge.

              **NOTE:** End date is exclusive.

          service_period_start_date: The service period start date (_in ISO-8601 format_) for the Charge.

          accounting_product_id: The Accounting Product ID assigned to the Charge.

          amount: Amount of the Charge. If `amount` is provided, then `units` and `unitPrice` must
              be omitted.

          bill_date: The date when the Charge will be added to a Bill.

          contract_id: The ID of a Contract on the Account that the Charge will be added to.

          description: The description added to the Bill line item for the Charge.

          entity_id: The ID of the Charge linked entity. For example, the ID of an Account Balance if
              a Balance Charge.

              **NOTE:** If `entityType` is `BALANCE`, you must provide the `entityId` of the
              Balance the Charge is for.

          notes: Used to enter information about the Charge for accounting purposes, such as the
              reason it was created. This information will not be added to a Bill line item
              for the Charge.

          unit_price: Unit price. If `amount` is omitted, then provide together with `units`. When
              `amount` is provided, `unitPrice` must be omitted.

          units: Number of units of the Charge. If `amount` is omitted, then provide together
              with `unitPrice`. When `amount` is provided, `units` must be omitted.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/charges/{id}",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "code": code,
                    "currency": currency,
                    "entity_type": entity_type,
                    "line_item_type": line_item_type,
                    "name": name,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "bill_date": bill_date,
                    "contract_id": contract_id,
                    "description": description,
                    "entity_id": entity_id,
                    "notes": notes,
                    "unit_price": unit_price,
                    "units": units,
                    "version": version,
                },
                charge_update_params.ChargeUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeUpdateResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        bill_date: Union[str, date] | Omit = omit,
        entity_id: str | Omit = omit,
        entity_type: Literal["AD_HOC", "BALANCE"] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        schedule_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ChargeListResponse, AsyncCursor[ChargeListResponse]]:
        """
        Retrieve a list of Charge entities

        Args:
          account_id: List Charge items for the Account UUID

          bill_date: List Charge items for the Bill Date

          entity_id: List Charge items for the Entity UUID

          entity_type: List Charge items for the EntityType

          ids: List of Charge UUIDs to retrieve

          next_token: nextToken for multi page retrievals

          page_size: Number of Charges to retrieve per page

          schedule_id: List Charge items for the Schedule UUID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/charges",
            page=AsyncCursor[ChargeListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "bill_date": bill_date,
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "schedule_id": schedule_id,
                    },
                    charge_list_params.ChargeListParams,
                ),
            ),
            model=ChargeListResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChargeDeleteResponse:
        """
        Delete the Charge for the given UUID.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/charges/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ChargeDeleteResponse,
        )


class ChargesResourceWithRawResponse:
    def __init__(self, charges: ChargesResource) -> None:
        self._charges = charges

        self.create = to_raw_response_wrapper(
            charges.create,
        )
        self.retrieve = to_raw_response_wrapper(
            charges.retrieve,
        )
        self.update = to_raw_response_wrapper(
            charges.update,
        )
        self.list = to_raw_response_wrapper(
            charges.list,
        )
        self.delete = to_raw_response_wrapper(
            charges.delete,
        )


class AsyncChargesResourceWithRawResponse:
    def __init__(self, charges: AsyncChargesResource) -> None:
        self._charges = charges

        self.create = async_to_raw_response_wrapper(
            charges.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            charges.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            charges.update,
        )
        self.list = async_to_raw_response_wrapper(
            charges.list,
        )
        self.delete = async_to_raw_response_wrapper(
            charges.delete,
        )


class ChargesResourceWithStreamingResponse:
    def __init__(self, charges: ChargesResource) -> None:
        self._charges = charges

        self.create = to_streamed_response_wrapper(
            charges.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            charges.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            charges.update,
        )
        self.list = to_streamed_response_wrapper(
            charges.list,
        )
        self.delete = to_streamed_response_wrapper(
            charges.delete,
        )


class AsyncChargesResourceWithStreamingResponse:
    def __init__(self, charges: AsyncChargesResource) -> None:
        self._charges = charges

        self.create = async_to_streamed_response_wrapper(
            charges.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            charges.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            charges.update,
        )
        self.list = async_to_streamed_response_wrapper(
            charges.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            charges.delete,
        )

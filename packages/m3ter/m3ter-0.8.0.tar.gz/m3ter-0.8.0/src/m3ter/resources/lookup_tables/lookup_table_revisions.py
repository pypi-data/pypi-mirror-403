# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from datetime import datetime
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
from ...types.lookup_tables import (
    lookup_table_revision_list_params,
    lookup_table_revision_create_params,
    lookup_table_revision_update_params,
    lookup_table_revision_update_status_params,
)
from ...types.lookup_tables.lookup_table_revision_response import LookupTableRevisionResponse

__all__ = ["LookupTableRevisionsResource", "AsyncLookupTableRevisionsResource"]


class LookupTableRevisionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LookupTableRevisionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return LookupTableRevisionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LookupTableRevisionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return LookupTableRevisionsResourceWithStreamingResponse(self)

    def create(
        self,
        lookup_table_id: str,
        *,
        org_id: str | None = None,
        fields: Iterable[lookup_table_revision_create_params.Field],
        keys: SequenceNotStr[str],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Create a new Revision for a Lookup Table.

        Fields and Keys for Revision schema: Use the `fields` parameter to define a
        Revision schema containing up to 10 number or string fields. Use the `keys`
        parameter to specify which are the key fields:

        - At least one field must be a non-key field and at least one a key field.
        - Up to 5 key fields can be defined.
        - Using multiple key fields: ensure that the order in which they are defined
          matches the order in which you want to use them in any Lookup functions that
          reference the Revision's Lookup Table, because this is the order in which they
          will be passed into the function. The order of non-key fields is not
          constrained in this way.

        Revision status: when you first create a Lookup Table Revision it has DRAFT
        status. Use the
        [Update LookupTableRevision Status](www.m3ter.com/docs/api#tag/LookupTableRevision/operation/UpdateLookupTableRevisionStatus)
        call to change a Revision's status.

        Args:
          fields: The list of fields of the Lookup Table Revision.

          keys: The ordered keys of the Lookup Table Revision.

          name: Descriptive name for the Lookup Table Revision.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          start_date: The start date of the Lookup Table Revision.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        return self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions",
            body=maybe_transform(
                {
                    "fields": fields,
                    "keys": keys,
                    "name": name,
                    "custom_fields": custom_fields,
                    "start_date": start_date,
                    "version": version,
                },
                lookup_table_revision_create_params.LookupTableRevisionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Retrieve a Lookup Table Revision for the given UUID.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        fields: Iterable[lookup_table_revision_update_params.Field],
        keys: SequenceNotStr[str],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Update a Lookup Table Revision for the given UUID.

        **NOTE:** If you've already added data to a Lookup Table Revision - see the
        following
        [Lookup Table Revision Data](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData)
        section - then you won't be able to change the Revision's field schema and
        you'll receive an error if you try do this. Create a new Revision instead, or
        delete the data items first.

        Args:
          fields: The list of fields of the Lookup Table Revision.

          keys: The ordered keys of the Lookup Table Revision.

          name: Descriptive name for the Lookup Table Revision.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          start_date: The start date of the Lookup Table Revision.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}",
            body=maybe_transform(
                {
                    "fields": fields,
                    "keys": keys,
                    "name": name,
                    "custom_fields": custom_fields,
                    "start_date": start_date,
                    "version": version,
                },
                lookup_table_revision_update_params.LookupTableRevisionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    def list(
        self,
        lookup_table_id: str,
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
    ) -> SyncCursor[LookupTableRevisionResponse]:
        """
        List LookupTableRevision entities

        Args:
          ids: List of Lookup Table Revision IDs to retrieve

          next_token: Token to supply for multi page retrievals

          page_size: Number of LookupTable to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions",
            page=SyncCursor[LookupTableRevisionResponse],
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
                    lookup_table_revision_list_params.LookupTableRevisionListParams,
                ),
            ),
            model=LookupTableRevisionResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Delete the Lookup Table Revision for the given UUID.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    def update_status(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        status: Literal["DRAFT", "PUBLISHED", "ARCHIVED"] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Update the status of a Lookup Table Revision for the given UUID.

        Args:
          status: Status of a Lookup Table Revision

          version: The version of the LookupTableRevision.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}/status",
            body=maybe_transform(
                {
                    "status": status,
                    "version": version,
                },
                lookup_table_revision_update_status_params.LookupTableRevisionUpdateStatusParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )


class AsyncLookupTableRevisionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLookupTableRevisionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLookupTableRevisionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLookupTableRevisionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncLookupTableRevisionsResourceWithStreamingResponse(self)

    async def create(
        self,
        lookup_table_id: str,
        *,
        org_id: str | None = None,
        fields: Iterable[lookup_table_revision_create_params.Field],
        keys: SequenceNotStr[str],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Create a new Revision for a Lookup Table.

        Fields and Keys for Revision schema: Use the `fields` parameter to define a
        Revision schema containing up to 10 number or string fields. Use the `keys`
        parameter to specify which are the key fields:

        - At least one field must be a non-key field and at least one a key field.
        - Up to 5 key fields can be defined.
        - Using multiple key fields: ensure that the order in which they are defined
          matches the order in which you want to use them in any Lookup functions that
          reference the Revision's Lookup Table, because this is the order in which they
          will be passed into the function. The order of non-key fields is not
          constrained in this way.

        Revision status: when you first create a Lookup Table Revision it has DRAFT
        status. Use the
        [Update LookupTableRevision Status](www.m3ter.com/docs/api#tag/LookupTableRevision/operation/UpdateLookupTableRevisionStatus)
        call to change a Revision's status.

        Args:
          fields: The list of fields of the Lookup Table Revision.

          keys: The ordered keys of the Lookup Table Revision.

          name: Descriptive name for the Lookup Table Revision.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          start_date: The start date of the Lookup Table Revision.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        return await self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions",
            body=await async_maybe_transform(
                {
                    "fields": fields,
                    "keys": keys,
                    "name": name,
                    "custom_fields": custom_fields,
                    "start_date": start_date,
                    "version": version,
                },
                lookup_table_revision_create_params.LookupTableRevisionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Retrieve a Lookup Table Revision for the given UUID.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        fields: Iterable[lookup_table_revision_update_params.Field],
        keys: SequenceNotStr[str],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        start_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Update a Lookup Table Revision for the given UUID.

        **NOTE:** If you've already added data to a Lookup Table Revision - see the
        following
        [Lookup Table Revision Data](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData)
        section - then you won't be able to change the Revision's field schema and
        you'll receive an error if you try do this. Create a new Revision instead, or
        delete the data items first.

        Args:
          fields: The list of fields of the Lookup Table Revision.

          keys: The ordered keys of the Lookup Table Revision.

          name: Descriptive name for the Lookup Table Revision.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          start_date: The start date of the Lookup Table Revision.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}",
            body=await async_maybe_transform(
                {
                    "fields": fields,
                    "keys": keys,
                    "name": name,
                    "custom_fields": custom_fields,
                    "start_date": start_date,
                    "version": version,
                },
                lookup_table_revision_update_params.LookupTableRevisionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    def list(
        self,
        lookup_table_id: str,
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
    ) -> AsyncPaginator[LookupTableRevisionResponse, AsyncCursor[LookupTableRevisionResponse]]:
        """
        List LookupTableRevision entities

        Args:
          ids: List of Lookup Table Revision IDs to retrieve

          next_token: Token to supply for multi page retrievals

          page_size: Number of LookupTable to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions",
            page=AsyncCursor[LookupTableRevisionResponse],
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
                    lookup_table_revision_list_params.LookupTableRevisionListParams,
                ),
            ),
            model=LookupTableRevisionResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Delete the Lookup Table Revision for the given UUID.

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
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )

    async def update_status(
        self,
        id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        status: Literal["DRAFT", "PUBLISHED", "ARCHIVED"] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionResponse:
        """
        Update the status of a Lookup Table Revision for the given UUID.

        Args:
          status: Status of a Lookup Table Revision

          version: The version of the LookupTableRevision.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not lookup_table_id:
            raise ValueError(f"Expected a non-empty value for `lookup_table_id` but received {lookup_table_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{id}/status",
            body=await async_maybe_transform(
                {
                    "status": status,
                    "version": version,
                },
                lookup_table_revision_update_status_params.LookupTableRevisionUpdateStatusParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionResponse,
        )


class LookupTableRevisionsResourceWithRawResponse:
    def __init__(self, lookup_table_revisions: LookupTableRevisionsResource) -> None:
        self._lookup_table_revisions = lookup_table_revisions

        self.create = to_raw_response_wrapper(
            lookup_table_revisions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            lookup_table_revisions.retrieve,
        )
        self.update = to_raw_response_wrapper(
            lookup_table_revisions.update,
        )
        self.list = to_raw_response_wrapper(
            lookup_table_revisions.list,
        )
        self.delete = to_raw_response_wrapper(
            lookup_table_revisions.delete,
        )
        self.update_status = to_raw_response_wrapper(
            lookup_table_revisions.update_status,
        )


class AsyncLookupTableRevisionsResourceWithRawResponse:
    def __init__(self, lookup_table_revisions: AsyncLookupTableRevisionsResource) -> None:
        self._lookup_table_revisions = lookup_table_revisions

        self.create = async_to_raw_response_wrapper(
            lookup_table_revisions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            lookup_table_revisions.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            lookup_table_revisions.update,
        )
        self.list = async_to_raw_response_wrapper(
            lookup_table_revisions.list,
        )
        self.delete = async_to_raw_response_wrapper(
            lookup_table_revisions.delete,
        )
        self.update_status = async_to_raw_response_wrapper(
            lookup_table_revisions.update_status,
        )


class LookupTableRevisionsResourceWithStreamingResponse:
    def __init__(self, lookup_table_revisions: LookupTableRevisionsResource) -> None:
        self._lookup_table_revisions = lookup_table_revisions

        self.create = to_streamed_response_wrapper(
            lookup_table_revisions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            lookup_table_revisions.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            lookup_table_revisions.update,
        )
        self.list = to_streamed_response_wrapper(
            lookup_table_revisions.list,
        )
        self.delete = to_streamed_response_wrapper(
            lookup_table_revisions.delete,
        )
        self.update_status = to_streamed_response_wrapper(
            lookup_table_revisions.update_status,
        )


class AsyncLookupTableRevisionsResourceWithStreamingResponse:
    def __init__(self, lookup_table_revisions: AsyncLookupTableRevisionsResource) -> None:
        self._lookup_table_revisions = lookup_table_revisions

        self.create = async_to_streamed_response_wrapper(
            lookup_table_revisions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            lookup_table_revisions.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            lookup_table_revisions.update,
        )
        self.list = async_to_streamed_response_wrapper(
            lookup_table_revisions.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            lookup_table_revisions.delete,
        )
        self.update_status = async_to_streamed_response_wrapper(
            lookup_table_revisions.update_status,
        )

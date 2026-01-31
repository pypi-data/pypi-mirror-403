# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union

import httpx

from ...types import (
    lookup_table_list_params,
    lookup_table_create_params,
    lookup_table_update_params,
    lookup_table_retrieve_params,
)
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
from .lookup_table_revisions import (
    LookupTableRevisionsResource,
    AsyncLookupTableRevisionsResource,
    LookupTableRevisionsResourceWithRawResponse,
    AsyncLookupTableRevisionsResourceWithRawResponse,
    LookupTableRevisionsResourceWithStreamingResponse,
    AsyncLookupTableRevisionsResourceWithStreamingResponse,
)
from ...types.lookup_table_response import LookupTableResponse
from .lookup_table_revision_data.lookup_table_revision_data import (
    LookupTableRevisionDataResource,
    AsyncLookupTableRevisionDataResource,
    LookupTableRevisionDataResourceWithRawResponse,
    AsyncLookupTableRevisionDataResourceWithRawResponse,
    LookupTableRevisionDataResourceWithStreamingResponse,
    AsyncLookupTableRevisionDataResourceWithStreamingResponse,
)

__all__ = ["LookupTablesResource", "AsyncLookupTablesResource"]


class LookupTablesResource(SyncAPIResource):
    @cached_property
    def lookup_table_revisions(self) -> LookupTableRevisionsResource:
        return LookupTableRevisionsResource(self._client)

    @cached_property
    def lookup_table_revision_data(self) -> LookupTableRevisionDataResource:
        return LookupTableRevisionDataResource(self._client)

    @cached_property
    def with_raw_response(self) -> LookupTablesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return LookupTablesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LookupTablesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return LookupTablesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableResponse:
        """
        Create a new Lookup Table.

        Args:
          code: Code of the Lookup Table - unique short code used to identify the Lookup Table.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          name: Descriptive name for the Lookup Table.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/lookuptables",
            body=maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "custom_fields": custom_fields,
                    "version": version,
                },
                lookup_table_create_params.LookupTableCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableResponse:
        """
        Retrieve a Lookup Table by UUID.

        Args:
          additional: Comma separated list of additional non-default fields to be included in the
              response. For example,if you want to include the active Revision for the Lookup
              Tables returned, set `additional=activeRevision` in the query.

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
            f"/organizations/{org_id}/lookuptables/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"additional": additional}, lookup_table_retrieve_params.LookupTableRetrieveParams
                ),
            ),
            cast_to=LookupTableResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableResponse:
        """
        Update the Lookup Table with the given UUID.

        Args:
          code: Code of the Lookup Table - unique short code used to identify the Lookup Table.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          name: Descriptive name for the Lookup Table.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/lookuptables/{id}",
            body=maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "custom_fields": custom_fields,
                    "version": version,
                },
                lookup_table_update_params.LookupTableUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        codes: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[LookupTableResponse]:
        """
        Retrieve a list Lookup Tables created for the Organization:

        - Returned list can be filtered by Lookup Table `code` query parameter.
        - If you want to include any non-default fields for the returned Lookup Tables,
          use the additional query parameter to specify which you want to include in the
          response.

        Args:
          additional: Comma separated list of additional non-default fields to be included in the
              response. For example,if you want to include the active Revision for each of the
              Lookup Tables returned, set `additional=activeRevision` in the query.

          codes: List of Lookup Table codes to retrieve.

          next_token: Token to supply for multi page retrievals.

          page_size: Number of Lookup Tables to retrieve per page.

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
            f"/organizations/{org_id}/lookuptables",
            page=SyncCursor[LookupTableResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "additional": additional,
                        "codes": codes,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    lookup_table_list_params.LookupTableListParams,
                ),
            ),
            model=LookupTableResponse,
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
    ) -> LookupTableResponse:
        """
        Delete the Lookup Table with the given UUID.

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
            f"/organizations/{org_id}/lookuptables/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableResponse,
        )


class AsyncLookupTablesResource(AsyncAPIResource):
    @cached_property
    def lookup_table_revisions(self) -> AsyncLookupTableRevisionsResource:
        return AsyncLookupTableRevisionsResource(self._client)

    @cached_property
    def lookup_table_revision_data(self) -> AsyncLookupTableRevisionDataResource:
        return AsyncLookupTableRevisionDataResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncLookupTablesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLookupTablesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLookupTablesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncLookupTablesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableResponse:
        """
        Create a new Lookup Table.

        Args:
          code: Code of the Lookup Table - unique short code used to identify the Lookup Table.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          name: Descriptive name for the Lookup Table.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/lookuptables",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "custom_fields": custom_fields,
                    "version": version,
                },
                lookup_table_create_params.LookupTableCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableResponse:
        """
        Retrieve a Lookup Table by UUID.

        Args:
          additional: Comma separated list of additional non-default fields to be included in the
              response. For example,if you want to include the active Revision for the Lookup
              Tables returned, set `additional=activeRevision` in the query.

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
            f"/organizations/{org_id}/lookuptables/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"additional": additional}, lookup_table_retrieve_params.LookupTableRetrieveParams
                ),
            ),
            cast_to=LookupTableResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableResponse:
        """
        Update the Lookup Table with the given UUID.

        Args:
          code: Code of the Lookup Table - unique short code used to identify the Lookup Table.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          name: Descriptive name for the Lookup Table.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/lookuptables/{id}",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "custom_fields": custom_fields,
                    "version": version,
                },
                lookup_table_update_params.LookupTableUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        codes: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LookupTableResponse, AsyncCursor[LookupTableResponse]]:
        """
        Retrieve a list Lookup Tables created for the Organization:

        - Returned list can be filtered by Lookup Table `code` query parameter.
        - If you want to include any non-default fields for the returned Lookup Tables,
          use the additional query parameter to specify which you want to include in the
          response.

        Args:
          additional: Comma separated list of additional non-default fields to be included in the
              response. For example,if you want to include the active Revision for each of the
              Lookup Tables returned, set `additional=activeRevision` in the query.

          codes: List of Lookup Table codes to retrieve.

          next_token: Token to supply for multi page retrievals.

          page_size: Number of Lookup Tables to retrieve per page.

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
            f"/organizations/{org_id}/lookuptables",
            page=AsyncCursor[LookupTableResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "additional": additional,
                        "codes": codes,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    lookup_table_list_params.LookupTableListParams,
                ),
            ),
            model=LookupTableResponse,
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
    ) -> LookupTableResponse:
        """
        Delete the Lookup Table with the given UUID.

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
            f"/organizations/{org_id}/lookuptables/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableResponse,
        )


class LookupTablesResourceWithRawResponse:
    def __init__(self, lookup_tables: LookupTablesResource) -> None:
        self._lookup_tables = lookup_tables

        self.create = to_raw_response_wrapper(
            lookup_tables.create,
        )
        self.retrieve = to_raw_response_wrapper(
            lookup_tables.retrieve,
        )
        self.update = to_raw_response_wrapper(
            lookup_tables.update,
        )
        self.list = to_raw_response_wrapper(
            lookup_tables.list,
        )
        self.delete = to_raw_response_wrapper(
            lookup_tables.delete,
        )

    @cached_property
    def lookup_table_revisions(self) -> LookupTableRevisionsResourceWithRawResponse:
        return LookupTableRevisionsResourceWithRawResponse(self._lookup_tables.lookup_table_revisions)

    @cached_property
    def lookup_table_revision_data(self) -> LookupTableRevisionDataResourceWithRawResponse:
        return LookupTableRevisionDataResourceWithRawResponse(self._lookup_tables.lookup_table_revision_data)


class AsyncLookupTablesResourceWithRawResponse:
    def __init__(self, lookup_tables: AsyncLookupTablesResource) -> None:
        self._lookup_tables = lookup_tables

        self.create = async_to_raw_response_wrapper(
            lookup_tables.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            lookup_tables.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            lookup_tables.update,
        )
        self.list = async_to_raw_response_wrapper(
            lookup_tables.list,
        )
        self.delete = async_to_raw_response_wrapper(
            lookup_tables.delete,
        )

    @cached_property
    def lookup_table_revisions(self) -> AsyncLookupTableRevisionsResourceWithRawResponse:
        return AsyncLookupTableRevisionsResourceWithRawResponse(self._lookup_tables.lookup_table_revisions)

    @cached_property
    def lookup_table_revision_data(self) -> AsyncLookupTableRevisionDataResourceWithRawResponse:
        return AsyncLookupTableRevisionDataResourceWithRawResponse(self._lookup_tables.lookup_table_revision_data)


class LookupTablesResourceWithStreamingResponse:
    def __init__(self, lookup_tables: LookupTablesResource) -> None:
        self._lookup_tables = lookup_tables

        self.create = to_streamed_response_wrapper(
            lookup_tables.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            lookup_tables.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            lookup_tables.update,
        )
        self.list = to_streamed_response_wrapper(
            lookup_tables.list,
        )
        self.delete = to_streamed_response_wrapper(
            lookup_tables.delete,
        )

    @cached_property
    def lookup_table_revisions(self) -> LookupTableRevisionsResourceWithStreamingResponse:
        return LookupTableRevisionsResourceWithStreamingResponse(self._lookup_tables.lookup_table_revisions)

    @cached_property
    def lookup_table_revision_data(self) -> LookupTableRevisionDataResourceWithStreamingResponse:
        return LookupTableRevisionDataResourceWithStreamingResponse(self._lookup_tables.lookup_table_revision_data)


class AsyncLookupTablesResourceWithStreamingResponse:
    def __init__(self, lookup_tables: AsyncLookupTablesResource) -> None:
        self._lookup_tables = lookup_tables

        self.create = async_to_streamed_response_wrapper(
            lookup_tables.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            lookup_tables.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            lookup_tables.update,
        )
        self.list = async_to_streamed_response_wrapper(
            lookup_tables.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            lookup_tables.delete,
        )

    @cached_property
    def lookup_table_revisions(self) -> AsyncLookupTableRevisionsResourceWithStreamingResponse:
        return AsyncLookupTableRevisionsResourceWithStreamingResponse(self._lookup_tables.lookup_table_revisions)

    @cached_property
    def lookup_table_revision_data(self) -> AsyncLookupTableRevisionDataResourceWithStreamingResponse:
        return AsyncLookupTableRevisionDataResourceWithStreamingResponse(self._lookup_tables.lookup_table_revision_data)

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable
from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.lookup_tables import (
    lookup_table_revision_data_copy_params,
    lookup_table_revision_data_update_params,
    lookup_table_revision_data_archieve_params,
    lookup_table_revision_data_retrieve_params,
    lookup_table_revision_data_delete_key_params,
    lookup_table_revision_data_update_key_params,
    lookup_table_revision_data_generate_download_url_params,
)
from .lookup_table_revision_data_jobs import (
    LookupTableRevisionDataJobsResource,
    AsyncLookupTableRevisionDataJobsResource,
    LookupTableRevisionDataJobsResourceWithRawResponse,
    AsyncLookupTableRevisionDataJobsResourceWithRawResponse,
    LookupTableRevisionDataJobsResourceWithStreamingResponse,
    AsyncLookupTableRevisionDataJobsResourceWithStreamingResponse,
)
from ....types.lookup_tables.lookup_table_revision_data_copy_response import LookupTableRevisionDataCopyResponse
from ....types.lookup_tables.lookup_table_revision_data_delete_response import LookupTableRevisionDataDeleteResponse
from ....types.lookup_tables.lookup_table_revision_data_update_response import LookupTableRevisionDataUpdateResponse
from ....types.lookup_tables.lookup_table_revision_data_archieve_response import LookupTableRevisionDataArchieveResponse
from ....types.lookup_tables.lookup_table_revision_data_retrieve_response import LookupTableRevisionDataRetrieveResponse
from ....types.lookup_tables.lookup_table_revision_data_delete_key_response import (
    LookupTableRevisionDataDeleteKeyResponse,
)
from ....types.lookup_tables.lookup_table_revision_data_update_key_response import (
    LookupTableRevisionDataUpdateKeyResponse,
)
from ....types.lookup_tables.lookup_table_revision_data_retrieve_key_response import (
    LookupTableRevisionDataRetrieveKeyResponse,
)
from ....types.lookup_tables.lookup_table_revision_data_generate_download_url_response import (
    LookupTableRevisionDataGenerateDownloadURLResponse,
)

__all__ = ["LookupTableRevisionDataResource", "AsyncLookupTableRevisionDataResource"]


class LookupTableRevisionDataResource(SyncAPIResource):
    @cached_property
    def lookup_table_revision_data_jobs(self) -> LookupTableRevisionDataJobsResource:
        return LookupTableRevisionDataJobsResource(self._client)

    @cached_property
    def with_raw_response(self) -> LookupTableRevisionDataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return LookupTableRevisionDataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LookupTableRevisionDataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return LookupTableRevisionDataResourceWithStreamingResponse(self)

    def retrieve(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        additional: SequenceNotStr[str] | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataRetrieveResponse:
        """
        List Lookup Table Revision Data items for the given UUID.

        Args:
          additional: Comma separated list of additional fields. For example, you can use
              `additional=lookupKey` to get the lookup key returned for each Data item. You
              can then use a lookup key for the Get/Upsert/Delete data entry endpoints in this
              section.

          limit: The maximum number of Data items to return. Defaults to 2000. You can set this
              to return fewer items if required.

              If you expect the Revision to contain more than 2000 Data items, you can use the
              [Trigger Downlad URL Job](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/TriggerDownloadJob)
              to download the Lookup Table Revision Data.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "additional": additional,
                        "limit": limit,
                    },
                    lookup_table_revision_data_retrieve_params.LookupTableRevisionDataRetrieveParams,
                ),
            ),
            cast_to=LookupTableRevisionDataRetrieveResponse,
        )

    def update(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        items: Iterable[Dict[str, object]],
        additional: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataUpdateResponse:
        """
        Create/update the Lookup Table Revision Data for the given UUID.

        Args:
          items: The data for a lookup table revision

          additional: Comma separated list of additional fields. For example, you can use
              `additional=lookupKey` to get the lookup key returned for each Data item. You
              can then use a lookup key for the Get/Upsert/Delete data entry endpoints in this
              section.

          version: The version of the LookupTableRevisionData.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data",
            body=maybe_transform(
                {
                    "items": items,
                    "version": version,
                },
                lookup_table_revision_data_update_params.LookupTableRevisionDataUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"additional": additional},
                    lookup_table_revision_data_update_params.LookupTableRevisionDataUpdateParams,
                ),
            ),
            cast_to=LookupTableRevisionDataUpdateResponse,
        )

    def delete(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataDeleteResponse:
        """
        Delete the Lookup Table Revision Data for the given UUID.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataDeleteResponse,
        )

    def archieve(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        content_type: Literal["application/jsonl", "text/csv"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataArchieveResponse:
        """
        Get a URL which you can use to download the data for the specified archived
        Lookup Table Revision:

        - The `contentType` request parameter is required.
        - The returned URL is presigned - you can copy it into a browser and the data
          file is downloaded locally.
        - The upload URL is time limited - the `expiry` time is given in the response
          and the URL is valid for **_one hour_**.

        Args:
          content_type: The content type

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/archived",
            body=maybe_transform(
                {"content_type": content_type},
                lookup_table_revision_data_archieve_params.LookupTableRevisionDataArchieveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataArchieveResponse,
        )

    def copy(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        revision_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataCopyResponse:
        """
        Copy the Lookup Table Revision Data from a source Revision to an optional target
        Revision:

        - If you omit a target `revisionId`, then the source Revision and its Data is
          duplicated. The new Revision is given the source Revision's name appended with
          "Copy" but is assigned a new unique id.
        - If you specify a target `revisionId` to copy the source Revision and its Data
          to, you must ensure that the target Revision has a Data schema that matches
          the source Revision's Data schema otherwise you'll receive an error

        Args:
          revision_id: The target Revision id that the source Revision's data will be copied to.
              _(Optional)_

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/copy",
            body=maybe_transform(
                {"revision_id": revision_id}, lookup_table_revision_data_copy_params.LookupTableRevisionDataCopyParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataCopyResponse,
        )

    def delete_key(
        self,
        lookup_key: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        lookup_table_revision_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataDeleteKeyResponse:
        """
        Delete a Lookup Table Revision Data entry by lookup key.

        **NOTES:**

        - To obtain the lookup key for a Revision's data items, use the
          [Get LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionData)
          endpoint in this section and use the `additional=lookupKey` query parameter.
        - If the Revision's Data schema uses multiple key fields, enter these as a
          comma-separated list for the `lookupKey` path parameter: .../key1,key2,key3
          and so on. Importantly, multiple keys must be _entered in the same order_ as
          they are configured in the Revision's Data schema.

        Args:
          version: The version of the Lookup Table Revision Data.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        if not lookup_key:
            raise ValueError(f"Expected a non-empty value for `lookup_key` but received {lookup_key!r}")
        return self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/{lookup_key}",
            body=maybe_transform(
                {"version": version},
                lookup_table_revision_data_delete_key_params.LookupTableRevisionDataDeleteKeyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataDeleteKeyResponse,
        )

    def generate_download_url(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        content_length: int,
        content_type: Literal["application/jsonl", "text/csv"],
        file_name: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataGenerateDownloadURLResponse:
        """
        Generate a URL which can be used to upload a data file for creating or updating
        the Lookup Table Revision's data:

        - An upload URL is returned together with an UPLOAD `jobId`.
        - You can then upload your data file using a PUT request using the returned
          upload URL as the endpoint. For the PUT request, map the headers returned and
          their values and in the request body select the specified CSV or JSONL file
          containing the Revision Data to upload.
        - You can use the returned UPLOAD `jobId` with the
          [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
          or the
          [Get LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionDataJobResponse)
          endpoints for any follow-up or troubleshooting.

        **Important:**

        - The `contentLength` request parameter is required.
        - The upload URL is time limited - it is valid for **_one minute_**.

        Args:
          content_length: The size of the file body in bytes. For example: `"contentLength": 485`, where
              485 is the size in bytes of the file to upload.

          content_type: The content type

          file_name: The name of the file to be uploaded.

          version: Version of the Lookup Table Revision Data.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/generateuploadurl",
            body=maybe_transform(
                {
                    "content_length": content_length,
                    "content_type": content_type,
                    "file_name": file_name,
                    "version": version,
                },
                lookup_table_revision_data_generate_download_url_params.LookupTableRevisionDataGenerateDownloadURLParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataGenerateDownloadURLResponse,
        )

    def retrieve_key(
        self,
        lookup_key: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        lookup_table_revision_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataRetrieveKeyResponse:
        """
        Retrieve a Lookup Table Revision Data item for the given lookup key.

        **NOTES:**

        - To obtain the lookup key for a Revision's data items, use the
          [Get LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionData)
          endpoint in this section and use the `additional=lookupKey` query parameter.
        - If the Revision's Data schema uses multiple key fields, enter these as a
          comma-separated list for the `lookupKey` path parameter: .../key1,key2,key3
          and so on. Importantly, multiple keys must be _entered in the same order_ as
          they are configured in the Revision's Data schema.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        if not lookup_key:
            raise ValueError(f"Expected a non-empty value for `lookup_key` but received {lookup_key!r}")
        return self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/{lookup_key}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataRetrieveKeyResponse,
        )

    def update_key(
        self,
        lookup_key: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        lookup_table_revision_id: str,
        item: Dict[str, object],
        additional: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataUpdateKeyResponse:
        """
        Create/update a Lookup Table Revision Data item by lookup key.

        **NOTES:**

        - To obtain the lookup key for a Revision's data items, use the
          [Get LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionData)
          endpoint in this section and use the `additional=lookupKey` query parameter.
        - If the Revision's Data schema uses multiple key fields, enter these as a
          comma-separated list for the `lookupKey` path parameter: .../key1,key2,key3
          and so on. Importantly, multiple keys must be _entered in the same order_ as
          they are configured in the Revision's Data schema.

        Args:
          item: The item you want to upsert

          additional: Comma separated list of additional fields. For example, you can use
              `additional=lookupKey` to get the lookup key returned for the Data item.

          version: The version of the LookupTableRevisionData.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        if not lookup_key:
            raise ValueError(f"Expected a non-empty value for `lookup_key` but received {lookup_key!r}")
        return self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/{lookup_key}",
            body=maybe_transform(
                {
                    "item": item,
                    "version": version,
                },
                lookup_table_revision_data_update_key_params.LookupTableRevisionDataUpdateKeyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"additional": additional},
                    lookup_table_revision_data_update_key_params.LookupTableRevisionDataUpdateKeyParams,
                ),
            ),
            cast_to=LookupTableRevisionDataUpdateKeyResponse,
        )


class AsyncLookupTableRevisionDataResource(AsyncAPIResource):
    @cached_property
    def lookup_table_revision_data_jobs(self) -> AsyncLookupTableRevisionDataJobsResource:
        return AsyncLookupTableRevisionDataJobsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncLookupTableRevisionDataResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLookupTableRevisionDataResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLookupTableRevisionDataResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncLookupTableRevisionDataResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        additional: SequenceNotStr[str] | Omit = omit,
        limit: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataRetrieveResponse:
        """
        List Lookup Table Revision Data items for the given UUID.

        Args:
          additional: Comma separated list of additional fields. For example, you can use
              `additional=lookupKey` to get the lookup key returned for each Data item. You
              can then use a lookup key for the Get/Upsert/Delete data entry endpoints in this
              section.

          limit: The maximum number of Data items to return. Defaults to 2000. You can set this
              to return fewer items if required.

              If you expect the Revision to contain more than 2000 Data items, you can use the
              [Trigger Downlad URL Job](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/TriggerDownloadJob)
              to download the Lookup Table Revision Data.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return await self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "additional": additional,
                        "limit": limit,
                    },
                    lookup_table_revision_data_retrieve_params.LookupTableRevisionDataRetrieveParams,
                ),
            ),
            cast_to=LookupTableRevisionDataRetrieveResponse,
        )

    async def update(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        items: Iterable[Dict[str, object]],
        additional: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataUpdateResponse:
        """
        Create/update the Lookup Table Revision Data for the given UUID.

        Args:
          items: The data for a lookup table revision

          additional: Comma separated list of additional fields. For example, you can use
              `additional=lookupKey` to get the lookup key returned for each Data item. You
              can then use a lookup key for the Get/Upsert/Delete data entry endpoints in this
              section.

          version: The version of the LookupTableRevisionData.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return await self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data",
            body=await async_maybe_transform(
                {
                    "items": items,
                    "version": version,
                },
                lookup_table_revision_data_update_params.LookupTableRevisionDataUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"additional": additional},
                    lookup_table_revision_data_update_params.LookupTableRevisionDataUpdateParams,
                ),
            ),
            cast_to=LookupTableRevisionDataUpdateResponse,
        )

    async def delete(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataDeleteResponse:
        """
        Delete the Lookup Table Revision Data for the given UUID.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return await self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataDeleteResponse,
        )

    async def archieve(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        content_type: Literal["application/jsonl", "text/csv"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataArchieveResponse:
        """
        Get a URL which you can use to download the data for the specified archived
        Lookup Table Revision:

        - The `contentType` request parameter is required.
        - The returned URL is presigned - you can copy it into a browser and the data
          file is downloaded locally.
        - The upload URL is time limited - the `expiry` time is given in the response
          and the URL is valid for **_one hour_**.

        Args:
          content_type: The content type

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/archived",
            body=await async_maybe_transform(
                {"content_type": content_type},
                lookup_table_revision_data_archieve_params.LookupTableRevisionDataArchieveParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataArchieveResponse,
        )

    async def copy(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        revision_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataCopyResponse:
        """
        Copy the Lookup Table Revision Data from a source Revision to an optional target
        Revision:

        - If you omit a target `revisionId`, then the source Revision and its Data is
          duplicated. The new Revision is given the source Revision's name appended with
          "Copy" but is assigned a new unique id.
        - If you specify a target `revisionId` to copy the source Revision and its Data
          to, you must ensure that the target Revision has a Data schema that matches
          the source Revision's Data schema otherwise you'll receive an error

        Args:
          revision_id: The target Revision id that the source Revision's data will be copied to.
              _(Optional)_

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/copy",
            body=await async_maybe_transform(
                {"revision_id": revision_id}, lookup_table_revision_data_copy_params.LookupTableRevisionDataCopyParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataCopyResponse,
        )

    async def delete_key(
        self,
        lookup_key: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        lookup_table_revision_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataDeleteKeyResponse:
        """
        Delete a Lookup Table Revision Data entry by lookup key.

        **NOTES:**

        - To obtain the lookup key for a Revision's data items, use the
          [Get LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionData)
          endpoint in this section and use the `additional=lookupKey` query parameter.
        - If the Revision's Data schema uses multiple key fields, enter these as a
          comma-separated list for the `lookupKey` path parameter: .../key1,key2,key3
          and so on. Importantly, multiple keys must be _entered in the same order_ as
          they are configured in the Revision's Data schema.

        Args:
          version: The version of the Lookup Table Revision Data.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        if not lookup_key:
            raise ValueError(f"Expected a non-empty value for `lookup_key` but received {lookup_key!r}")
        return await self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/{lookup_key}",
            body=await async_maybe_transform(
                {"version": version},
                lookup_table_revision_data_delete_key_params.LookupTableRevisionDataDeleteKeyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataDeleteKeyResponse,
        )

    async def generate_download_url(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        content_length: int,
        content_type: Literal["application/jsonl", "text/csv"],
        file_name: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataGenerateDownloadURLResponse:
        """
        Generate a URL which can be used to upload a data file for creating or updating
        the Lookup Table Revision's data:

        - An upload URL is returned together with an UPLOAD `jobId`.
        - You can then upload your data file using a PUT request using the returned
          upload URL as the endpoint. For the PUT request, map the headers returned and
          their values and in the request body select the specified CSV or JSONL file
          containing the Revision Data to upload.
        - You can use the returned UPLOAD `jobId` with the
          [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
          or the
          [Get LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionDataJobResponse)
          endpoints for any follow-up or troubleshooting.

        **Important:**

        - The `contentLength` request parameter is required.
        - The upload URL is time limited - it is valid for **_one minute_**.

        Args:
          content_length: The size of the file body in bytes. For example: `"contentLength": 485`, where
              485 is the size in bytes of the file to upload.

          content_type: The content type

          file_name: The name of the file to be uploaded.

          version: Version of the Lookup Table Revision Data.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/generateuploadurl",
            body=await async_maybe_transform(
                {
                    "content_length": content_length,
                    "content_type": content_type,
                    "file_name": file_name,
                    "version": version,
                },
                lookup_table_revision_data_generate_download_url_params.LookupTableRevisionDataGenerateDownloadURLParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataGenerateDownloadURLResponse,
        )

    async def retrieve_key(
        self,
        lookup_key: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        lookup_table_revision_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataRetrieveKeyResponse:
        """
        Retrieve a Lookup Table Revision Data item for the given lookup key.

        **NOTES:**

        - To obtain the lookup key for a Revision's data items, use the
          [Get LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionData)
          endpoint in this section and use the `additional=lookupKey` query parameter.
        - If the Revision's Data schema uses multiple key fields, enter these as a
          comma-separated list for the `lookupKey` path parameter: .../key1,key2,key3
          and so on. Importantly, multiple keys must be _entered in the same order_ as
          they are configured in the Revision's Data schema.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        if not lookup_key:
            raise ValueError(f"Expected a non-empty value for `lookup_key` but received {lookup_key!r}")
        return await self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/{lookup_key}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataRetrieveKeyResponse,
        )

    async def update_key(
        self,
        lookup_key: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        lookup_table_revision_id: str,
        item: Dict[str, object],
        additional: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LookupTableRevisionDataUpdateKeyResponse:
        """
        Create/update a Lookup Table Revision Data item by lookup key.

        **NOTES:**

        - To obtain the lookup key for a Revision's data items, use the
          [Get LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionData)
          endpoint in this section and use the `additional=lookupKey` query parameter.
        - If the Revision's Data schema uses multiple key fields, enter these as a
          comma-separated list for the `lookupKey` path parameter: .../key1,key2,key3
          and so on. Importantly, multiple keys must be _entered in the same order_ as
          they are configured in the Revision's Data schema.

        Args:
          item: The item you want to upsert

          additional: Comma separated list of additional fields. For example, you can use
              `additional=lookupKey` to get the lookup key returned for the Data item.

          version: The version of the LookupTableRevisionData.

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
        if not lookup_table_revision_id:
            raise ValueError(
                f"Expected a non-empty value for `lookup_table_revision_id` but received {lookup_table_revision_id!r}"
            )
        if not lookup_key:
            raise ValueError(f"Expected a non-empty value for `lookup_key` but received {lookup_key!r}")
        return await self._put(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/{lookup_key}",
            body=await async_maybe_transform(
                {
                    "item": item,
                    "version": version,
                },
                lookup_table_revision_data_update_key_params.LookupTableRevisionDataUpdateKeyParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"additional": additional},
                    lookup_table_revision_data_update_key_params.LookupTableRevisionDataUpdateKeyParams,
                ),
            ),
            cast_to=LookupTableRevisionDataUpdateKeyResponse,
        )


class LookupTableRevisionDataResourceWithRawResponse:
    def __init__(self, lookup_table_revision_data: LookupTableRevisionDataResource) -> None:
        self._lookup_table_revision_data = lookup_table_revision_data

        self.retrieve = to_raw_response_wrapper(
            lookup_table_revision_data.retrieve,
        )
        self.update = to_raw_response_wrapper(
            lookup_table_revision_data.update,
        )
        self.delete = to_raw_response_wrapper(
            lookup_table_revision_data.delete,
        )
        self.archieve = to_raw_response_wrapper(
            lookup_table_revision_data.archieve,
        )
        self.copy = to_raw_response_wrapper(
            lookup_table_revision_data.copy,
        )
        self.delete_key = to_raw_response_wrapper(
            lookup_table_revision_data.delete_key,
        )
        self.generate_download_url = to_raw_response_wrapper(
            lookup_table_revision_data.generate_download_url,
        )
        self.retrieve_key = to_raw_response_wrapper(
            lookup_table_revision_data.retrieve_key,
        )
        self.update_key = to_raw_response_wrapper(
            lookup_table_revision_data.update_key,
        )

    @cached_property
    def lookup_table_revision_data_jobs(self) -> LookupTableRevisionDataJobsResourceWithRawResponse:
        return LookupTableRevisionDataJobsResourceWithRawResponse(
            self._lookup_table_revision_data.lookup_table_revision_data_jobs
        )


class AsyncLookupTableRevisionDataResourceWithRawResponse:
    def __init__(self, lookup_table_revision_data: AsyncLookupTableRevisionDataResource) -> None:
        self._lookup_table_revision_data = lookup_table_revision_data

        self.retrieve = async_to_raw_response_wrapper(
            lookup_table_revision_data.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            lookup_table_revision_data.update,
        )
        self.delete = async_to_raw_response_wrapper(
            lookup_table_revision_data.delete,
        )
        self.archieve = async_to_raw_response_wrapper(
            lookup_table_revision_data.archieve,
        )
        self.copy = async_to_raw_response_wrapper(
            lookup_table_revision_data.copy,
        )
        self.delete_key = async_to_raw_response_wrapper(
            lookup_table_revision_data.delete_key,
        )
        self.generate_download_url = async_to_raw_response_wrapper(
            lookup_table_revision_data.generate_download_url,
        )
        self.retrieve_key = async_to_raw_response_wrapper(
            lookup_table_revision_data.retrieve_key,
        )
        self.update_key = async_to_raw_response_wrapper(
            lookup_table_revision_data.update_key,
        )

    @cached_property
    def lookup_table_revision_data_jobs(self) -> AsyncLookupTableRevisionDataJobsResourceWithRawResponse:
        return AsyncLookupTableRevisionDataJobsResourceWithRawResponse(
            self._lookup_table_revision_data.lookup_table_revision_data_jobs
        )


class LookupTableRevisionDataResourceWithStreamingResponse:
    def __init__(self, lookup_table_revision_data: LookupTableRevisionDataResource) -> None:
        self._lookup_table_revision_data = lookup_table_revision_data

        self.retrieve = to_streamed_response_wrapper(
            lookup_table_revision_data.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            lookup_table_revision_data.update,
        )
        self.delete = to_streamed_response_wrapper(
            lookup_table_revision_data.delete,
        )
        self.archieve = to_streamed_response_wrapper(
            lookup_table_revision_data.archieve,
        )
        self.copy = to_streamed_response_wrapper(
            lookup_table_revision_data.copy,
        )
        self.delete_key = to_streamed_response_wrapper(
            lookup_table_revision_data.delete_key,
        )
        self.generate_download_url = to_streamed_response_wrapper(
            lookup_table_revision_data.generate_download_url,
        )
        self.retrieve_key = to_streamed_response_wrapper(
            lookup_table_revision_data.retrieve_key,
        )
        self.update_key = to_streamed_response_wrapper(
            lookup_table_revision_data.update_key,
        )

    @cached_property
    def lookup_table_revision_data_jobs(self) -> LookupTableRevisionDataJobsResourceWithStreamingResponse:
        return LookupTableRevisionDataJobsResourceWithStreamingResponse(
            self._lookup_table_revision_data.lookup_table_revision_data_jobs
        )


class AsyncLookupTableRevisionDataResourceWithStreamingResponse:
    def __init__(self, lookup_table_revision_data: AsyncLookupTableRevisionDataResource) -> None:
        self._lookup_table_revision_data = lookup_table_revision_data

        self.retrieve = async_to_streamed_response_wrapper(
            lookup_table_revision_data.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            lookup_table_revision_data.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            lookup_table_revision_data.delete,
        )
        self.archieve = async_to_streamed_response_wrapper(
            lookup_table_revision_data.archieve,
        )
        self.copy = async_to_streamed_response_wrapper(
            lookup_table_revision_data.copy,
        )
        self.delete_key = async_to_streamed_response_wrapper(
            lookup_table_revision_data.delete_key,
        )
        self.generate_download_url = async_to_streamed_response_wrapper(
            lookup_table_revision_data.generate_download_url,
        )
        self.retrieve_key = async_to_streamed_response_wrapper(
            lookup_table_revision_data.retrieve_key,
        )
        self.update_key = async_to_streamed_response_wrapper(
            lookup_table_revision_data.update_key,
        )

    @cached_property
    def lookup_table_revision_data_jobs(self) -> AsyncLookupTableRevisionDataJobsResourceWithStreamingResponse:
        return AsyncLookupTableRevisionDataJobsResourceWithStreamingResponse(
            self._lookup_table_revision_data.lookup_table_revision_data_jobs
        )

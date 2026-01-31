# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....pagination import SyncCursor, AsyncCursor
from ...._base_client import AsyncPaginator, make_request_options
from ....types.lookup_tables.lookup_table_revision_data import (
    lookup_table_revision_data_job_list_params,
    lookup_table_revision_data_job_download_params,
)
from ....types.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_job_list_response import (
    LookupTableRevisionDataJobListResponse,
)
from ....types.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_job_delete_response import (
    LookupTableRevisionDataJobDeleteResponse,
)
from ....types.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_job_download_response import (
    LookupTableRevisionDataJobDownloadResponse,
)
from ....types.lookup_tables.lookup_table_revision_data.lookup_table_revision_data_job_retrieve_response import (
    LookupTableRevisionDataJobRetrieveResponse,
)

__all__ = ["LookupTableRevisionDataJobsResource", "AsyncLookupTableRevisionDataJobsResource"]


class LookupTableRevisionDataJobsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LookupTableRevisionDataJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return LookupTableRevisionDataJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LookupTableRevisionDataJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return LookupTableRevisionDataJobsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
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
    ) -> LookupTableRevisionDataJobRetrieveResponse:
        """
        Get the Lookup Table Revision Data job Response for given job id.

        **NOTE:** Use the
        [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
        endpoint to list the Data job Responses for a specific Revision.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataJobRetrieveResponse,
        )

    def list(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[LookupTableRevisionDataJobListResponse]:
        """
        List the Lookup Table Revision Data job Responses for the given Lookup Table
        Revision.

        There are four types of Revision Data jobs:

        - **COPY**. Job runs when you use the
          [Copy LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/CopyLookupTableRevisionData)
          endpoint which returns the `jobId`.
        - **UPLOAD**. Job runs when you use the
          [Generate LookupTableRevisionData Upload URL](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GenerateLookupTableDataUploadUrl)
          endpoint which returns the `jobId`.
        - **DOWNLOAD**. Job runs when you use the
          [](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/TriggerLookupTableRevisionDataDownloadJob)
          endpoint which returns the `jobId`.
        - **ARCHIVE**. Job runs when you either manually change a DRAFT Revision to
          PUBLISHED using the
          [Update LookupTableRevision Status](https://www.m3ter.com/docs/api#tag/LookupTableRevision/operation/UpdateLookupTableRevisionStatus)
          endpoint or you publish a DRAFT Revision and the existing PUBLISHED Revision
          is archived.

        **NOTE:** This endpoint returns the id of each Data job. You then use:

        - The
          [Get LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionDataJobResponse)
          endpoint to retrieve a specific Data job Response.
        - The
          [Delete LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/DeleteLookupTableRevisionDataJobResponse)
          to delete a specific Data job Response.

        Args:
          next_token: The nextToken for multi page retrievals

          page_size: The number of Lookup Table Revision Data Job Responses to retrieve per page.

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
        return self._get_api_list(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs",
            page=SyncCursor[LookupTableRevisionDataJobListResponse],
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
                    lookup_table_revision_data_job_list_params.LookupTableRevisionDataJobListParams,
                ),
            ),
            model=LookupTableRevisionDataJobListResponse,
        )

    def delete(
        self,
        id: str,
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
    ) -> LookupTableRevisionDataJobDeleteResponse:
        """
        Delete the LookupTableRevisionData Job Response for given job id.

        **NOTE:** Use the
        [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
        endpoint to list the Data job Responses for a specific Revision.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataJobDeleteResponse,
        )

    def download(
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
    ) -> LookupTableRevisionDataJobDownloadResponse:
        """Trigger an URL job to download the Lookup Table Revision Data.

        The URL download
        Data `jobId` is returned and you can then use the
        [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
        endpoint or the
        [Get LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionDataJobResponse)
        endpoint to retrieve the URL and perform the Revision data Download.

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
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs/download",
            body=maybe_transform(
                {"content_type": content_type},
                lookup_table_revision_data_job_download_params.LookupTableRevisionDataJobDownloadParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataJobDownloadResponse,
        )


class AsyncLookupTableRevisionDataJobsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLookupTableRevisionDataJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLookupTableRevisionDataJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLookupTableRevisionDataJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncLookupTableRevisionDataJobsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
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
    ) -> LookupTableRevisionDataJobRetrieveResponse:
        """
        Get the Lookup Table Revision Data job Response for given job id.

        **NOTE:** Use the
        [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
        endpoint to list the Data job Responses for a specific Revision.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataJobRetrieveResponse,
        )

    def list(
        self,
        lookup_table_revision_id: str,
        *,
        org_id: str | None = None,
        lookup_table_id: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LookupTableRevisionDataJobListResponse, AsyncCursor[LookupTableRevisionDataJobListResponse]]:
        """
        List the Lookup Table Revision Data job Responses for the given Lookup Table
        Revision.

        There are four types of Revision Data jobs:

        - **COPY**. Job runs when you use the
          [Copy LookupTableRevisionData](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/CopyLookupTableRevisionData)
          endpoint which returns the `jobId`.
        - **UPLOAD**. Job runs when you use the
          [Generate LookupTableRevisionData Upload URL](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GenerateLookupTableDataUploadUrl)
          endpoint which returns the `jobId`.
        - **DOWNLOAD**. Job runs when you use the
          [](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/TriggerLookupTableRevisionDataDownloadJob)
          endpoint which returns the `jobId`.
        - **ARCHIVE**. Job runs when you either manually change a DRAFT Revision to
          PUBLISHED using the
          [Update LookupTableRevision Status](https://www.m3ter.com/docs/api#tag/LookupTableRevision/operation/UpdateLookupTableRevisionStatus)
          endpoint or you publish a DRAFT Revision and the existing PUBLISHED Revision
          is archived.

        **NOTE:** This endpoint returns the id of each Data job. You then use:

        - The
          [Get LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionDataJobResponse)
          endpoint to retrieve a specific Data job Response.
        - The
          [Delete LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/DeleteLookupTableRevisionDataJobResponse)
          to delete a specific Data job Response.

        Args:
          next_token: The nextToken for multi page retrievals

          page_size: The number of Lookup Table Revision Data Job Responses to retrieve per page.

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
        return self._get_api_list(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs",
            page=AsyncCursor[LookupTableRevisionDataJobListResponse],
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
                    lookup_table_revision_data_job_list_params.LookupTableRevisionDataJobListParams,
                ),
            ),
            model=LookupTableRevisionDataJobListResponse,
        )

    async def delete(
        self,
        id: str,
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
    ) -> LookupTableRevisionDataJobDeleteResponse:
        """
        Delete the LookupTableRevisionData Job Response for given job id.

        **NOTE:** Use the
        [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
        endpoint to list the Data job Responses for a specific Revision.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataJobDeleteResponse,
        )

    async def download(
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
    ) -> LookupTableRevisionDataJobDownloadResponse:
        """Trigger an URL job to download the Lookup Table Revision Data.

        The URL download
        Data `jobId` is returned and you can then use the
        [List LookupTableRevisionData Jobs](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/ListLookupTableRevisionDataJobs)
        endpoint or the
        [Get LookupTableRevisionData Job Response](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/GetLookupTableRevisionDataJobResponse)
        endpoint to retrieve the URL and perform the Revision data Download.

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
            f"/organizations/{org_id}/lookuptables/{lookup_table_id}/revisions/{lookup_table_revision_id}/data/jobs/download",
            body=await async_maybe_transform(
                {"content_type": content_type},
                lookup_table_revision_data_job_download_params.LookupTableRevisionDataJobDownloadParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LookupTableRevisionDataJobDownloadResponse,
        )


class LookupTableRevisionDataJobsResourceWithRawResponse:
    def __init__(self, lookup_table_revision_data_jobs: LookupTableRevisionDataJobsResource) -> None:
        self._lookup_table_revision_data_jobs = lookup_table_revision_data_jobs

        self.retrieve = to_raw_response_wrapper(
            lookup_table_revision_data_jobs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            lookup_table_revision_data_jobs.list,
        )
        self.delete = to_raw_response_wrapper(
            lookup_table_revision_data_jobs.delete,
        )
        self.download = to_raw_response_wrapper(
            lookup_table_revision_data_jobs.download,
        )


class AsyncLookupTableRevisionDataJobsResourceWithRawResponse:
    def __init__(self, lookup_table_revision_data_jobs: AsyncLookupTableRevisionDataJobsResource) -> None:
        self._lookup_table_revision_data_jobs = lookup_table_revision_data_jobs

        self.retrieve = async_to_raw_response_wrapper(
            lookup_table_revision_data_jobs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            lookup_table_revision_data_jobs.list,
        )
        self.delete = async_to_raw_response_wrapper(
            lookup_table_revision_data_jobs.delete,
        )
        self.download = async_to_raw_response_wrapper(
            lookup_table_revision_data_jobs.download,
        )


class LookupTableRevisionDataJobsResourceWithStreamingResponse:
    def __init__(self, lookup_table_revision_data_jobs: LookupTableRevisionDataJobsResource) -> None:
        self._lookup_table_revision_data_jobs = lookup_table_revision_data_jobs

        self.retrieve = to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.list,
        )
        self.delete = to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.delete,
        )
        self.download = to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.download,
        )


class AsyncLookupTableRevisionDataJobsResourceWithStreamingResponse:
    def __init__(self, lookup_table_revision_data_jobs: AsyncLookupTableRevisionDataJobsResource) -> None:
        self._lookup_table_revision_data_jobs = lookup_table_revision_data_jobs

        self.retrieve = async_to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.delete,
        )
        self.download = async_to_streamed_response_wrapper(
            lookup_table_revision_data_jobs.download,
        )

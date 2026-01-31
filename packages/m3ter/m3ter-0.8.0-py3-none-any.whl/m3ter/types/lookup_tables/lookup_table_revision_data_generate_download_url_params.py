# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataGenerateDownloadURLParams"]


class LookupTableRevisionDataGenerateDownloadURLParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    content_length: Required[Annotated[int, PropertyInfo(alias="contentLength")]]
    """The size of the file body in bytes.

    For example: `"contentLength": 485`, where 485 is the size in bytes of the file
    to upload.
    """

    content_type: Required[Annotated[Literal["application/jsonl", "text/csv"], PropertyInfo(alias="contentType")]]
    """The content type"""

    file_name: Required[Annotated[str, PropertyInfo(alias="fileName")]]
    """The name of the file to be uploaded."""

    version: int
    """Version of the Lookup Table Revision Data."""

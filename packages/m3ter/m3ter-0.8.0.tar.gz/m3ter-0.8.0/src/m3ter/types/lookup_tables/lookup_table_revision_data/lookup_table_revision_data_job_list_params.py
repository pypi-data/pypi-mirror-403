# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataJobListParams"]


class LookupTableRevisionDataJobListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The nextToken for multi page retrievals"""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """The number of Lookup Table Revision Data Job Responses to retrieve per page."""

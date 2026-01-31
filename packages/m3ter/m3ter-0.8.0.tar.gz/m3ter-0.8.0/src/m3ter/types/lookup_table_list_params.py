# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["LookupTableListParams"]


class LookupTableListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    additional: SequenceNotStr[str]
    """
    Comma separated list of additional non-default fields to be included in the
    response. For example,if you want to include the active Revision for each of the
    Lookup Tables returned, set `additional=activeRevision` in the query.
    """

    codes: SequenceNotStr[str]
    """List of Lookup Table codes to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """Token to supply for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Lookup Tables to retrieve per page."""

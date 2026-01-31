# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionUpdateStatusParams"]


class LookupTableRevisionUpdateStatusParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    status: Literal["DRAFT", "PUBLISHED", "ARCHIVED"]
    """Status of a Lookup Table Revision"""

    version: int
    """The version of the LookupTableRevision."""

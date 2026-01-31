# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataDeleteKeyParams"]


class LookupTableRevisionDataDeleteKeyParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    lookup_table_revision_id: Required[Annotated[str, PropertyInfo(alias="lookupTableRevisionId")]]

    version: int
    """The version of the Lookup Table Revision Data."""

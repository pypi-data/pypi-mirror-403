# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataUpdateKeyParams"]


class LookupTableRevisionDataUpdateKeyParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    lookup_table_revision_id: Required[Annotated[str, PropertyInfo(alias="lookupTableRevisionId")]]

    item: Required[Dict[str, object]]
    """The item you want to upsert"""

    additional: SequenceNotStr[str]
    """Comma separated list of additional fields.

    For example, you can use `additional=lookupKey` to get the lookup key returned
    for the Data item.
    """

    version: int
    """The version of the LookupTableRevisionData."""

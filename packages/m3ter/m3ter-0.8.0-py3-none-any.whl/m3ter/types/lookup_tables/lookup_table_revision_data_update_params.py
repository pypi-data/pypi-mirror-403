# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable
from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataUpdateParams"]


class LookupTableRevisionDataUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    items: Required[Iterable[Dict[str, object]]]
    """The data for a lookup table revision"""

    additional: SequenceNotStr[str]
    """Comma separated list of additional fields.

    For example, you can use `additional=lookupKey` to get the lookup key returned
    for each Data item. You can then use a lookup key for the Get/Upsert/Delete data
    entry endpoints in this section.
    """

    version: int
    """The version of the LookupTableRevisionData."""

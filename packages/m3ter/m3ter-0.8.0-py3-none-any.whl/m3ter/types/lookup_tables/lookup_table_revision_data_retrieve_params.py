# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataRetrieveParams"]


class LookupTableRevisionDataRetrieveParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    additional: SequenceNotStr[str]
    """Comma separated list of additional fields.

    For example, you can use `additional=lookupKey` to get the lookup key returned
    for each Data item. You can then use a lookup key for the Get/Upsert/Delete data
    entry endpoints in this section.
    """

    limit: int
    """The maximum number of Data items to return.

    Defaults to 2000. You can set this to return fewer items if required.

    If you expect the Revision to contain more than 2000 Data items, you can use the
    [Trigger Downlad URL Job](https://www.m3ter.com/docs/api#tag/LookupTableRevisionData/operation/TriggerDownloadJob)
    to download the Lookup Table Revision Data.
    """

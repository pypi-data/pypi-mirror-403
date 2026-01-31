# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionDataCopyParams"]


class LookupTableRevisionDataCopyParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    revision_id: Annotated[str, PropertyInfo(alias="revisionId")]
    """The target Revision id that the source Revision's data will be copied to.

    _(Optional)_
    """

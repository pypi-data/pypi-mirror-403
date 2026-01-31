# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date
from typing_extensions import Literal, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["ChargeListParams"]


class ChargeListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """List Charge items for the Account UUID"""

    bill_date: Annotated[Union[str, date], PropertyInfo(alias="billDate", format="iso8601")]
    """List Charge items for the Bill Date"""

    entity_id: Annotated[str, PropertyInfo(alias="entityId")]
    """List Charge items for the Entity UUID"""

    entity_type: Annotated[Literal["AD_HOC", "BALANCE"], PropertyInfo(alias="entityType")]
    """List Charge items for the EntityType"""

    ids: SequenceNotStr[str]
    """List of Charge UUIDs to retrieve"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """nextToken for multi page retrievals"""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Charges to retrieve per page"""

    schedule_id: Annotated[str, PropertyInfo(alias="scheduleId")]
    """List Charge items for the Schedule UUID"""

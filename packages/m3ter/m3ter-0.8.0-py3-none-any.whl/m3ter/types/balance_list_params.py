# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["BalanceListParams"]


class BalanceListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """The unique identifier (UUID) for the end customer's account."""

    contract: str

    contract_id: Annotated[str, PropertyInfo(alias="contractId")]
    """Filter Balances by contract id.

    Use '' with accountId to fetch unlinked balances.
    """

    end_date_end: Annotated[str, PropertyInfo(alias="endDateEnd")]
    """Only include Balances with end dates earlier than this date.

    If a Balance has a rollover amount configured, then the `rolloverEndDate` will
    be used as the end date.
    """

    end_date_start: Annotated[str, PropertyInfo(alias="endDateStart")]
    """Only include Balances with end dates equal to or later than this date.

    If a Balance has a rollover amount configured, then the `rolloverEndDate` will
    be used as the end date.
    """

    ids: SequenceNotStr[str]
    """A list of unique identifiers (UUIDs) for specific Balances to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for retrieving the next page of Balances.

    It is used to fetch the next page of Balances in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """The maximum number of Balances to return per page."""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from datetime import date
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ContractUpdateParams", "UsageFilter"]


class ContractUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Required[Annotated[str, PropertyInfo(alias="accountId")]]
    """The unique identifier (UUID) of the Account associated with this Contract."""

    end_date: Required[Annotated[Union[str, date], PropertyInfo(alias="endDate", format="iso8601")]]
    """The exclusive end date of the Contract _(in ISO-8601 format)_.

    This means the Contract is active until midnight on the day **_before_** this
    date.
    """

    name: Required[str]
    """The name of the Contract."""

    start_date: Required[Annotated[Union[str, date], PropertyInfo(alias="startDate", format="iso8601")]]
    """The start date for the Contract _(in ISO-8601 format)_.

    This date is inclusive, meaning the Contract is active from this date onward.
    """

    apply_contract_period_limits: Annotated[bool, PropertyInfo(alias="applyContractPeriodLimits")]
    """
    For Contract billing, a boolean setting for restricting the charges billed to
    the period defined for the Contract:

    - **TRUE** - Contract billing for the Account will be restricted to charge
      amounts that fall within the defined Contract period.
    - **FALSE** - The period for amounts billed under the Contract will be
      determined by the Account Plan attached to the Account and linked to the
      Contract.(_Default_)
    """

    bill_grouping_key_id: Annotated[str, PropertyInfo(alias="billGroupingKeyId")]
    """The ID of the Bill Grouping Key assigned to the Contract.

    If you are implementing Contract Billing for an Account, use `billGroupingKey`
    to control how charges linked to Contracts on the Account will be billed:

    - **Independent Contract billing**. Assign an _exclusive_ Bill Grouping Key to
      the Contract - only charges due against the Account and linked to the single
      Contract will appear on a separate Bill.
    - **Collective Contract billing**. Assign the same _non-exclusive_ Bill Grouping
      Key to multiple Contracts - all charges due against the Account and linked to
      the multiple Contracts will appear together on a single Bill.
    """

    code: str
    """The short code of the Contract."""

    custom_fields: Annotated[Dict[str, Union[str, float]], PropertyInfo(alias="customFields")]
    """User defined fields enabling you to attach custom data.

    The value for a custom field can be either a string or a number.

    If `customFields` can also be defined for this entity at the Organizational
    level, `customField` values defined at individual level override values of
    `customFields` with the same name defined at Organization level.

    See
    [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
    in the m3ter documentation for more information.
    """

    description: str
    """The description of the Contract, which provides context and information."""

    purchase_order_number: Annotated[str, PropertyInfo(alias="purchaseOrderNumber")]
    """The Purchase Order Number associated with the Contract."""

    usage_filters: Annotated[Iterable[UsageFilter], PropertyInfo(alias="usageFilters")]
    """
    Use `usageFilters` to control Contract billing and charge at billing only for
    usage where Product Meter dimensions equal specific defined values:

    - Define Usage filters to either _include_ or _exclude_ charges for usage
      associated with specific Meter dimensions.
    - The Meter dimensions must be present in the data field schema of the Meter
      used to submit usage data measurements.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class UsageFilter(TypedDict, total=False):
    """Filters that determine which usage records are included in contract billing"""

    dimension_code: Required[Annotated[str, PropertyInfo(alias="dimensionCode")]]

    mode: Required[Literal["INCLUDE", "EXCLUDE"]]

    value: Required[str]

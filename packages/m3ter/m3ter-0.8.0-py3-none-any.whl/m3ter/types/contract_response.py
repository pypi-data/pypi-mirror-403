# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ContractResponse", "UsageFilter"]


class UsageFilter(BaseModel):
    """Filters that determine which usage records are included in contract billing"""

    dimension_code: str = FieldInfo(alias="dimensionCode")

    mode: Literal["INCLUDE", "EXCLUDE"]

    value: str


class ContractResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """The unique identifier (UUID) of the Account associated with this Contract."""

    apply_contract_period_limits: Optional[bool] = FieldInfo(alias="applyContractPeriodLimits", default=None)
    """
    For Contract billing, a boolean setting for restricting the charges billed to
    the period defined for the Contract:

    - **TRUE** - Contract billing for the Account will be restricted to charge
      amounts that fall within the defined Contract period.
    - **FALSE** - The period for amounts billed under the Contract will be
      determined by the Account Plan attached to the Account and linked to the
      Contract.(_Default_)
    """

    bill_grouping_key_id: Optional[str] = FieldInfo(alias="billGroupingKeyId", default=None)
    """The ID of the Bill Grouping Key assigned to the Contract."""

    code: Optional[str] = None
    """The short code of the Contract."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this Contract."""

    custom_fields: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="customFields", default=None)
    """User defined fields enabling you to attach custom data.

    The value for a custom field can be either a string or a number.

    If `customFields` can also be defined for this entity at the Organizational
    level,`customField` values defined at individual level override values of
    `customFields` with the same name defined at Organization level.

    See
    [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
    in the m3ter documentation for more information.
    """

    description: Optional[str] = None
    """The description of the Contract, which provides context and information."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the Contract was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO-8601 format)_ when the Contract was last modified."""

    end_date: Optional[date] = FieldInfo(alias="endDate", default=None)
    """The exclusive end date of the Contract _(in ISO-8601 format)_.

    This means the Contract is active until midnight on the day **_before_** this
    date.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this Contract."""

    name: Optional[str] = None
    """The name of the Contract."""

    purchase_order_number: Optional[str] = FieldInfo(alias="purchaseOrderNumber", default=None)
    """The Purchase Order Number associated with the Contract."""

    start_date: Optional[date] = FieldInfo(alias="startDate", default=None)
    """The start date for the Contract _(in ISO-8601 format)_.

    This date is inclusive, meaning the Contract is active from this date onward.
    """

    usage_filters: Optional[List[UsageFilter]] = FieldInfo(alias="usageFilters", default=None)
    """
    Used to control Contract billing and charge at billing only for usage where
    Product Meter dimensions equal specific defined values:

    - Usage filters are defined to either _include_ or _exclude_ charges for usage
      associated with specific Meter dimensions.
    - The Meter dimensions must be present in the data field schema of the Meter
      used to submit usage data measurements.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

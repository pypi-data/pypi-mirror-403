# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from datetime import date, datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ChargeSchedulePreviewParams"]


class ChargeSchedulePreviewParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bill_frequency: Required[
        Annotated[Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"], PropertyInfo(alias="billFrequency")]
    ]
    """Represents standard scheduling frequencies options for a job."""

    bill_frequency_interval: Required[Annotated[int, PropertyInfo(alias="billFrequencyInterval")]]
    """How often Bills are issued.

    For example, if billFrequency is `MONTHLY` and `billFrequencyInterval` is 3,
    Bills are issued every three months.
    """

    bill_in_advance: Required[Annotated[bool, PropertyInfo(alias="billInAdvance")]]
    """
    Used to specify how Charges created by the Balance Charge Schedule are billed -
    either in arrears or in advance:

    - Use `false` for billing in arrears.
    - Use `true` for billing in advance.
    """

    charge_description: Required[Annotated[str, PropertyInfo(alias="chargeDescription")]]
    """The description for Charges created by the Balance Charge Schedule.

    Used on Bills for Charge line items.
    """

    code: Required[str]
    """Unique short code for the Balance Charge Schedule."""

    currency: Required[str]
    """The currency of the Charges created by the Balance Charge Schedule."""

    name: Required[str]
    """The name of the Balance Charge Schedule."""

    service_period_end_date: Required[
        Annotated[Union[str, datetime], PropertyInfo(alias="servicePeriodEndDate", format="iso8601")]
    ]
    """
    The service period end date (_in ISO-8601 format_) of the Balance Charge
    Schedule.
    """

    service_period_start_date: Required[
        Annotated[Union[str, datetime], PropertyInfo(alias="servicePeriodStartDate", format="iso8601")]
    ]
    """
    The service period start date (_in ISO-8601 format)_ of the Balance Charge
    Schedule.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """nextToken for multi page retrievals"""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Charges to retrieve per page"""

    amount: float
    """The amount of each Charge created by the Balance Charge Schedule.

    Must be omitted if `units` and `unitPrice` are provided.
    """

    bill_epoch: Annotated[Union[str, date], PropertyInfo(alias="billEpoch", format="iso8601")]
    """
    Specify a billing cycle date (_in ISO-8601 format_) for when the first Bill is
    created for Balance Charges created by the Schedule, and also acts as a
    reference for when in the Schedule period subsequent Bills are created for the
    defined `billFrequency`. If left blank, then the relevant Epoch date from your
    Organization's configuration will be used as the billing cycle date instead.
    """

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

    unit_price: Annotated[float, PropertyInfo(alias="unitPrice")]
    """Unit price for Charge.

    Must be provided when `units` is used. Must be omitted when `amount` is used.
    """

    units: float
    """Number of units defined for the Charges created by the Schedule.

    Required when `unitPrice` is provided. Must be omitted when `amount` is used.
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

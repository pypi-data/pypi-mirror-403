# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ChargeScheduleCreateResponse"]


class ChargeScheduleCreateResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    charge_description: str = FieldInfo(alias="chargeDescription")
    """The description for Charges created by the Balance Charge Schedule.

    Used on Bills for Charge line items.
    """

    amount: Optional[float] = None
    """The amount of each Charge created by the Balance Charge Schedule."""

    balance_id: Optional[str] = FieldInfo(alias="balanceId", default=None)
    """
    The unique identifier (UUID) for the Balance this Balance Charge Schedule was
    created for.
    """

    bill_epoch: Optional[date] = FieldInfo(alias="billEpoch", default=None)
    """
    Specifies a billing cycle date (_in ISO-8601 format_) for when the first Bill is
    generated for Balance Charges created by the Schedule, and also acts as a
    reference for when in the Schedule period subsequent Bills are created for the
    defined `billFrequency`. If blank, then the relevant Epoch date from your
    Organization's configuration is used.
    """

    bill_frequency: Optional[Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"]] = FieldInfo(
        alias="billFrequency", default=None
    )
    """Represents standard scheduling frequencies options for a job."""

    bill_frequency_interval: Optional[int] = FieldInfo(alias="billFrequencyInterval", default=None)
    """How often Bills are issued.

    For example, if billFrequency is `MONTHLY` and `billFrequencyInterval` is 3,
    Bills are issued every three months.
    """

    bill_in_advance: Optional[bool] = FieldInfo(alias="billInAdvance", default=None)
    """
    Specifies how Charges created by the Balance Charge Schedule are billed - either
    in arrears or in advance:

    - If `false` then billing is in arrears.
    - If `true` then billing is in advance.
    """

    code: Optional[str] = None
    """Unique short code for the Balance Charge Schedule."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """
    The unique identifier (UUID) of the user who created the Balance Charge
    Schedule.
    """

    currency: Optional[str] = None
    """The currency of the Charges created by the Balance Charge Schedule."""

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

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """
    The date and time (_in ISO-8601 format_) when the Balance Charge Schedule was
    created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time (_in ISO-8601 format_) when the Balance Charge Schedule was
    last modified.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) for the user who last modified the Balance Charge
    Schedule.
    """

    name: Optional[str] = None
    """The name of the Balance Charge Schedule."""

    next_run: Optional[datetime] = FieldInfo(alias="nextRun", default=None)
    """
    The date and time (_in ISO-8601 format_) when the next Charge will be created by
    the Balance Charge Schedule.
    """

    previous_run: Optional[datetime] = FieldInfo(alias="previousRun", default=None)
    """
    The date and time (_in ISO-8601 format_) when the previous Charge was generated
    by the Balance Charge Schedule.
    """

    service_period_end_date: Optional[datetime] = FieldInfo(alias="servicePeriodEndDate", default=None)
    """
    The service period end date (_in ISO-8601 format_) of the Balance Charge
    Schedule.
    """

    service_period_start_date: Optional[datetime] = FieldInfo(alias="servicePeriodStartDate", default=None)
    """
    The service period start date (_in ISO-8601 format_) of the Balance Charge
    Schedule.
    """

    unit_price: Optional[float] = FieldInfo(alias="unitPrice", default=None)
    """Unit price. If the Charge was created with `amount` only, then will be null."""

    units: Optional[float] = None
    """Number of units.

    If the Charge was created with `amount` only, then will be null.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ChargeRetrieveResponse"]


class ChargeRetrieveResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """The ID of the Account the Charge was created for."""

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)
    """The Accounting Product ID assigned to the Charge."""

    amount: Optional[float] = None
    """The Charge amount.

    If `amount` has been defined, then `units` and `unitPrice` cannot be used.
    """

    bill_date: Optional[date] = FieldInfo(alias="billDate", default=None)
    """The date when the Charge will be added to a Bill."""

    bill_id: Optional[str] = FieldInfo(alias="billId", default=None)
    """The ID of the Bill created for this Charge."""

    code: Optional[str] = None
    """The unique short code of the Charge."""

    contract_id: Optional[str] = FieldInfo(alias="contractId", default=None)
    """The ID of a Contract on the Account that the Charge has been added to."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created the Charge."""

    currency: Optional[str] = None
    """Charge currency."""

    description: Optional[str] = None
    """The description added to the Bill line item for the Charge."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time (_in ISO-8601 format_) when the Charge was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time (_in ISO 8601 format_) when the Charge was last modified."""

    entity_id: Optional[str] = FieldInfo(alias="entityId", default=None)
    """The ID of the Charge linked entity.

    For example, the ID of an Account Balance if a Balance Charge.
    """

    entity_type: Optional[Literal["AD_HOC", "BALANCE"]] = FieldInfo(alias="entityType", default=None)
    """The entity type the Charge has been created for."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified the Charge."""

    line_item_type: Optional[Literal["BALANCE_FEE", "AD_HOC"]] = FieldInfo(alias="lineItemType", default=None)
    """The line item type used for billing a Charge."""

    name: Optional[str] = None
    """Name of the Charge. Added to the Bill line item description for Charge."""

    notes: Optional[str] = None
    """
    Information about the Charge for accounting purposes, such as the reason it was
    created. This information will not be added to the created Bill line item for
    the Charge.
    """

    schedule_id: Optional[str] = FieldInfo(alias="scheduleId", default=None)
    """The ID of the Balance Charge Schedule that created the Charge."""

    service_period_end_date: Optional[datetime] = FieldInfo(alias="servicePeriodEndDate", default=None)
    """The service period end date (_in ISO-8601 format_) for the Charge.

    **NOTE:** End date is exclusive.
    """

    service_period_start_date: Optional[datetime] = FieldInfo(alias="servicePeriodStartDate", default=None)
    """The service period start date (_in ISO-8601 format_) for the Charge ."""

    unit_price: Optional[float] = FieldInfo(alias="unitPrice", default=None)
    """Unit Price for the Charge. Provided together with `units`:

    - Null if the Charge was created with `amount` only.
    - If `units` and `unitPrice` are provided, `amount` cannot be used.
    """

    units: Optional[float] = None
    """Number of units of the Charge.

    Provided together with `unitPrice`. If `units` and `unitPrice` are provided,
    `amount` cannot be used.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

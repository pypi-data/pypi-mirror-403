# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ChargeCreateParams"]


class ChargeCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Required[Annotated[str, PropertyInfo(alias="accountId")]]
    """The ID of the Account the Charge is being created for."""

    code: Required[str]
    """Unique short code for the Charge."""

    currency: Required[str]
    """Charge currency."""

    entity_type: Required[Annotated[Literal["AD_HOC", "BALANCE"], PropertyInfo(alias="entityType")]]
    """The entity type the Charge has been created for."""

    line_item_type: Required[Annotated[Literal["BALANCE_FEE", "AD_HOC"], PropertyInfo(alias="lineItemType")]]
    """Available line item types that can be used for billing a Charge."""

    name: Required[str]
    """Name of the Charge. Added to the Bill line item description for this Charge."""

    service_period_end_date: Required[
        Annotated[Union[str, datetime], PropertyInfo(alias="servicePeriodEndDate", format="iso8601")]
    ]
    """The service period end date (_in ISO-8601 format_)for the Charge.

    **NOTE:** End date is exclusive.
    """

    service_period_start_date: Required[
        Annotated[Union[str, datetime], PropertyInfo(alias="servicePeriodStartDate", format="iso8601")]
    ]
    """The service period start date (_in ISO-8601 format_) for the Charge."""

    accounting_product_id: Annotated[str, PropertyInfo(alias="accountingProductId")]
    """The Accounting Product ID assigned to the Charge."""

    amount: float
    """Amount of the Charge.

    If `amount` is provided, then `units` and `unitPrice` must be omitted.
    """

    bill_date: Annotated[str, PropertyInfo(alias="billDate")]
    """The date when the Charge will be added to a Bill."""

    contract_id: Annotated[str, PropertyInfo(alias="contractId")]
    """The ID of a Contract on the Account that the Charge will be added to."""

    description: str
    """The description added to the Bill line item for the Charge."""

    entity_id: Annotated[str, PropertyInfo(alias="entityId")]
    """The ID of the Charge linked entity.

    For example, the ID of an Account Balance if a Balance Charge.

    **NOTE:** If `entityType` is `BALANCE`, you must provide the `entityId` of the
    Balance the Charge is for.
    """

    notes: str
    """
    Used to enter information about the Charge for accounting purposes, such as the
    reason it was created. This information will not be added to a Bill line item
    for the Charge.
    """

    unit_price: Annotated[float, PropertyInfo(alias="unitPrice")]
    """Unit price.

    If `amount` is omitted, then provide together with `units`. When `amount` is
    provided, `unitPrice` must be omitted.
    """

    units: float
    """Number of units of the Charge.

    If `amount` is omitted, then provide together with `unitPrice`. When `amount` is
    provided, `units` must be omitted.
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

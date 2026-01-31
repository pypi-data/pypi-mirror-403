# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["DebitLineItemResponse"]


class DebitLineItemResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    amount: Optional[float] = None

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this line item."""

    debit_reason_id: Optional[str] = FieldInfo(alias="debitReasonId", default=None)
    """The UUID of the debit reason for this debit line item."""

    description: Optional[str] = None

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the line item was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the line item was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this line item."""

    line_item_type: Optional[
        Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
            "AD_HOC",
        ]
    ] = FieldInfo(alias="lineItemType", default=None)

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)

    referenced_bill_id: Optional[str] = FieldInfo(alias="referencedBillId", default=None)

    referenced_line_item_id: Optional[str] = FieldInfo(alias="referencedLineItemId", default=None)

    service_period_end_date: Optional[datetime] = FieldInfo(alias="servicePeriodEndDate", default=None)

    service_period_start_date: Optional[datetime] = FieldInfo(alias="servicePeriodStartDate", default=None)

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

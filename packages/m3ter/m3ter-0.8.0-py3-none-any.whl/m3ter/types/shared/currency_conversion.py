# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["CurrencyConversion"]


class CurrencyConversion(BaseModel):
    """
    An array of currency conversion rates from Bill currency to Organization currency. For example, if Account is billed in GBP and Organization is set to USD, Bill line items are calculated in GBP and then converted to USD using the defined rate.
    """

    from_: str = FieldInfo(alias="from")
    """Currency to convert from. For example: GBP."""

    to: str
    """Currency to convert to. For example: USD."""

    multiplier: Optional[float] = None
    """Conversion rate between currencies."""

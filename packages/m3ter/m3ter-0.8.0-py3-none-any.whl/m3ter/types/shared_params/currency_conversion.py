# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["CurrencyConversion"]

_CurrencyConversionReservedKeywords = TypedDict(
    "_CurrencyConversionReservedKeywords",
    {
        "from": str,
    },
    total=False,
)


class CurrencyConversion(_CurrencyConversionReservedKeywords, total=False):
    """
    An array of currency conversion rates from Bill currency to Organization currency. For example, if Account is billed in GBP and Organization is set to USD, Bill line items are calculated in GBP and then converted to USD using the defined rate.
    """

    to: Required[str]
    """Currency to convert to. For example: USD."""

    multiplier: float
    """Conversion rate between currencies."""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["LookupTableRevisionUpdateParams", "Field"]


class LookupTableRevisionUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    lookup_table_id: Required[Annotated[str, PropertyInfo(alias="lookupTableId")]]

    fields: Required[Iterable[Field]]
    """The list of fields of the Lookup Table Revision."""

    keys: Required[SequenceNotStr[str]]
    """The ordered keys of the Lookup Table Revision."""

    name: Required[str]
    """Descriptive name for the Lookup Table Revision."""

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

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """The start date of the Lookup Table Revision."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class Field(TypedDict, total=False):
    """Field of a Lookup Table Revision"""

    type: Required[Literal["STRING", "NUMBER"]]
    """Type of a Lookup Table Revision Field"""

    name: str
    """The name of the field"""

# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LookupTableRevisionResponse", "Field"]


class Field(BaseModel):
    """Field of a Lookup Table Revision"""

    type: Literal["STRING", "NUMBER"]
    """Type of a Lookup Table Revision Field"""

    name: Optional[str] = None
    """The name of the field"""


class LookupTableRevisionResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created the Lookup Table Revision."""

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
    """The DateTime when the Lookup Table Revision was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the Lookup Table Revision was last modified."""

    fields: Optional[List[Field]] = None
    """The list of fields of the Lookup Table Revision."""

    item_count: Optional[int] = FieldInfo(alias="itemCount", default=None)

    keys: Optional[List[str]] = None
    """The ordered keys of the Lookup Table Revision"""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified the Lookup Table Revision."""

    name: Optional[str] = None
    """The name of the Lookup Table Revision."""

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """The start date of the Lookup Table Revision"""

    status: Optional[Literal["DRAFT", "PUBLISHED", "ARCHIVED"]] = None
    """Status of a Lookup Table Revision"""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

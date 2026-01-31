# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .lookup_tables.lookup_table_revision_response import LookupTableRevisionResponse

__all__ = ["LookupTableResponse"]


class LookupTableResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    active_revision: Optional[LookupTableRevisionResponse] = FieldInfo(alias="activeRevision", default=None)
    """Response containing a LookupTableRevision entity"""

    code: Optional[str] = None
    """The code of the Lookup Table"""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this Lookup Table."""

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
    """The DateTime when the Lookup Table was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the Lookup Table was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this Lookup Table."""

    name: Optional[str] = None
    """The name of the Lookup Table"""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

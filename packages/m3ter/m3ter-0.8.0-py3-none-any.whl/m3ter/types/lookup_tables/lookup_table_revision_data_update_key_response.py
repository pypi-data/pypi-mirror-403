# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LookupTableRevisionDataUpdateKeyResponse"]


class LookupTableRevisionDataUpdateKeyResponse(BaseModel):
    """Response containing data for a Lookup Table Revision"""

    items: List[Dict[str, object]]
    """The Lookup Table Revision Data."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created the Lookup Table Revision Data."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the Lookup Table Revision Data was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the Lookup Table Revision Data was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified the Lookup Table Revision Data."""

    version: Optional[int] = None
    """The version of the Lookup Table Revision Data."""

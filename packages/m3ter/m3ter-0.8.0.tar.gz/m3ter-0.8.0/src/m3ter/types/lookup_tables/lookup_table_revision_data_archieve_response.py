# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["LookupTableRevisionDataArchieveResponse"]


class LookupTableRevisionDataArchieveResponse(BaseModel):
    """Response containing the archive job URL details"""

    expiry: Optional[datetime] = None
    """The URL expiry time"""

    url: Optional[str] = None
    """The presigned URL"""

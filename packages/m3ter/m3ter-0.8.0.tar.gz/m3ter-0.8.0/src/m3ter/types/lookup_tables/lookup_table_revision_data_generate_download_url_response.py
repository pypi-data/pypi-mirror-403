# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LookupTableRevisionDataGenerateDownloadURLResponse"]


class LookupTableRevisionDataGenerateDownloadURLResponse(BaseModel):
    """Response containing the upload job URL details"""

    headers: Optional[Dict[str, str]] = None
    """The headers"""

    job_id: Optional[str] = FieldInfo(alias="jobId", default=None)
    """UUID of the upload job"""

    url: Optional[str] = None
    """The presigned URL"""

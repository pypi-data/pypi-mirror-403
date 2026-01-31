# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["LookupTableRevisionDataJobDownloadResponse"]


class LookupTableRevisionDataJobDownloadResponse(BaseModel):
    """Response containing the download job details"""

    job_id: Optional[str] = FieldInfo(alias="jobId", default=None)
    """UUID of the download job"""

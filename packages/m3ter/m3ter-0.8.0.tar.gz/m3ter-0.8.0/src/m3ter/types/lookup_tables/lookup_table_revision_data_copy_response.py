# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LookupTableRevisionDataCopyResponse"]


class LookupTableRevisionDataCopyResponse(BaseModel):
    job_id: Optional[str] = FieldInfo(alias="jobId", default=None)
    """UUID of the Revision Data copy job."""

    revision_id: Optional[str] = FieldInfo(alias="revisionId", default=None)
    """The ID of the destination Revision."""

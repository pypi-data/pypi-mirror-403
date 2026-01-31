# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["LookupTableRevisionDataJobRetrieveResponse"]


class LookupTableRevisionDataJobRetrieveResponse(BaseModel):
    """Response containing the LookupTableRevisionData job details"""

    id: Optional[str] = None
    """UUID of the Lookup Table Revision Data job."""

    destination_lookup_table_revision_id: Optional[str] = FieldInfo(
        alias="destinationLookupTableRevisionId", default=None
    )
    """
    UUID of the destination Lookup Table Revision if the Lookup Table Revision Data
    job is a COPY job.
    """

    download_url: Optional[str] = FieldInfo(alias="downloadUrl", default=None)
    """The download Url if the Lookup Table Revision Data job is a DOWNLOAD job."""

    download_url_expiry: Optional[str] = FieldInfo(alias="downloadUrlExpiry", default=None)
    """
    The download Url expiry if the Lookup Table Revision Data job is a DOWNLOAD job.
    """

    failure_reason: Optional[str] = FieldInfo(alias="failureReason", default=None)
    """The failure reason if the Lookup Table Revision Data job failed."""

    file_name: Optional[str] = FieldInfo(alias="fileName", default=None)
    """The file name for a Lookup Table Revision Data UPLOAD or DOWNLOAD job."""

    job_date: Optional[str] = FieldInfo(alias="jobDate", default=None)
    """The date when the Lookup Table Revision Data job was created."""

    lookup_table_id: Optional[str] = FieldInfo(alias="lookupTableId", default=None)
    """UUID of the Lookup Table."""

    lookup_table_revision_id: Optional[str] = FieldInfo(alias="lookupTableRevisionId", default=None)
    """UUID of the Lookup Table Revision."""

    status: Optional[Literal["PENDING", "FAILED", "SUCCEEDED"]] = None
    """The status of a job"""

    type: Optional[Literal["COPY", "UPLOAD", "DOWNLOAD", "ARCHIVE"]] = None

    version: Optional[int] = None
    """Version of the Lookup Table Revision Data job."""

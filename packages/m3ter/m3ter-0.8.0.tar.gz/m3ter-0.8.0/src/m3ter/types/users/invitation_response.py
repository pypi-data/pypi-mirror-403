# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["InvitationResponse"]


class InvitationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    accepted: Optional[bool] = None
    """Boolean indicating whether the user has accepted the invitation.

    - TRUE - the invite has been accepted.
    - FALSE - the invite has not yet been accepted.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The UUID of the user who created the invitation."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the invitation was created _(in ISO-8601 format)_."""

    dt_end_access: Optional[datetime] = FieldInfo(alias="dtEndAccess", default=None)
    """The date that access will end for the user _(in ISO-8601 format)_.

    If this is blank, there is no end date meaning that the user has permanent
    access.
    """

    dt_expiry: Optional[datetime] = FieldInfo(alias="dtExpiry", default=None)
    """The date when the invite expires _(in ISO-8601 format)_.

    After this date the invited user can no longer accept the invite. By default,
    any invite is valid for 30 days from the date the invite is sent.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the invitation was last modified _(in ISO-8601 format)_."""

    email: Optional[str] = None
    """The email address of the invitee.

    The invitation will be sent to this email address.
    """

    first_name: Optional[str] = FieldInfo(alias="firstName", default=None)
    """The first name of the invitee."""

    inviting_principal_id: Optional[str] = FieldInfo(alias="invitingPrincipalId", default=None)
    """The UUID of the user who sent the invite."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The UUID of the user who last modified the invitation."""

    last_name: Optional[str] = FieldInfo(alias="lastName", default=None)
    """The surname of the invitee."""

    permission_policy_ids: Optional[List[str]] = FieldInfo(alias="permissionPolicyIds", default=None)
    """The IDs of the permission policies the invited user has been assigned.

    This controls the access rights and privileges that this user will have when
    working in the m3ter Organization.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

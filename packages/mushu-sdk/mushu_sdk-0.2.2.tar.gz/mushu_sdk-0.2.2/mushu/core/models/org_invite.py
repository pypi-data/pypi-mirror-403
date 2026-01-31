from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.invite_status import InviteStatus
from ..models.invite_type import InviteType
from ..models.org_role import OrgRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="OrgInvite")


@_attrs_define
class OrgInvite:
    """Organization invite.

    Attributes:
        invite_id (str): Unique invite ID
        org_id (str): Organization ID
        invite_type (InviteType): Type of organization invite.
        role (OrgRole): Organization member role.
        invite_token (str): Token for accepting the invite
        status (InviteStatus): Status of an organization invite.
        invited_by (str): User ID who sent the invite
        created_at (str): When invite was created
        org_name (None | str | Unset): Organization name (for display)
        email (None | str | Unset): Email address (for email invites)
        expires_at (None | str | Unset): When invite expires
        accepted_at (None | str | Unset): When invite was accepted
        accepted_by (None | str | Unset): User ID who accepted
    """

    invite_id: str
    org_id: str
    invite_type: InviteType
    role: OrgRole
    invite_token: str
    status: InviteStatus
    invited_by: str
    created_at: str
    org_name: None | str | Unset = UNSET
    email: None | str | Unset = UNSET
    expires_at: None | str | Unset = UNSET
    accepted_at: None | str | Unset = UNSET
    accepted_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        invite_id = self.invite_id

        org_id = self.org_id

        invite_type = self.invite_type.value

        role = self.role.value

        invite_token = self.invite_token

        status = self.status.value

        invited_by = self.invited_by

        created_at = self.created_at

        org_name: None | str | Unset
        if isinstance(self.org_name, Unset):
            org_name = UNSET
        else:
            org_name = self.org_name

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = self.expires_at

        accepted_at: None | str | Unset
        if isinstance(self.accepted_at, Unset):
            accepted_at = UNSET
        else:
            accepted_at = self.accepted_at

        accepted_by: None | str | Unset
        if isinstance(self.accepted_by, Unset):
            accepted_by = UNSET
        else:
            accepted_by = self.accepted_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "invite_id": invite_id,
                "org_id": org_id,
                "invite_type": invite_type,
                "role": role,
                "invite_token": invite_token,
                "status": status,
                "invited_by": invited_by,
                "created_at": created_at,
            }
        )
        if org_name is not UNSET:
            field_dict["org_name"] = org_name
        if email is not UNSET:
            field_dict["email"] = email
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if accepted_at is not UNSET:
            field_dict["accepted_at"] = accepted_at
        if accepted_by is not UNSET:
            field_dict["accepted_by"] = accepted_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        invite_id = d.pop("invite_id")

        org_id = d.pop("org_id")

        invite_type = InviteType(d.pop("invite_type"))

        role = OrgRole(d.pop("role"))

        invite_token = d.pop("invite_token")

        status = InviteStatus(d.pop("status"))

        invited_by = d.pop("invited_by")

        created_at = d.pop("created_at")

        def _parse_org_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        org_name = _parse_org_name(d.pop("org_name", UNSET))

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_expires_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        def _parse_accepted_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        accepted_at = _parse_accepted_at(d.pop("accepted_at", UNSET))

        def _parse_accepted_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        accepted_by = _parse_accepted_by(d.pop("accepted_by", UNSET))

        org_invite = cls(
            invite_id=invite_id,
            org_id=org_id,
            invite_type=invite_type,
            role=role,
            invite_token=invite_token,
            status=status,
            invited_by=invited_by,
            created_at=created_at,
            org_name=org_name,
            email=email,
            expires_at=expires_at,
            accepted_at=accepted_at,
            accepted_by=accepted_by,
        )

        org_invite.additional_properties = d
        return org_invite

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

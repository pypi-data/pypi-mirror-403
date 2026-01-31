from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.org_role import OrgRole

T = TypeVar("T", bound="OrgMember")


@_attrs_define
class OrgMember:
    """Organization member.

    Attributes:
        user_id (str): User ID
        org_id (str): Organization ID
        role (OrgRole): Organization member role.
        joined_at (str): When user joined
    """

    user_id: str
    org_id: str
    role: OrgRole
    joined_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        org_id = self.org_id

        role = self.role.value

        joined_at = self.joined_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "org_id": org_id,
                "role": role,
                "joined_at": joined_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        org_id = d.pop("org_id")

        role = OrgRole(d.pop("role"))

        joined_at = d.pop("joined_at")

        org_member = cls(
            user_id=user_id,
            org_id=org_id,
            role=role,
            joined_at=joined_at,
        )

        org_member.additional_properties = d
        return org_member

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

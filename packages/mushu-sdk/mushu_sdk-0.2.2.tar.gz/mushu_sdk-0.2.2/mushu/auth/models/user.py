from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_type import UserType
from ..types import UNSET, Unset

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """User profile.

    Attributes:
        user_id (str): Unique user identifier
        user_type (UserType): Authentication provider type.
        created_at (str): ISO timestamp of account creation
        last_login (str): ISO timestamp of last login
        email (None | str | Unset): User email if available
        email_verified (bool | Unset): Whether email is verified Default: False.
        name (None | str | Unset): User's display name
    """

    user_id: str
    user_type: UserType
    created_at: str
    last_login: str
    email: None | str | Unset = UNSET
    email_verified: bool | Unset = False
    name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        user_type = self.user_type.value

        created_at = self.created_at

        last_login = self.last_login

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        email_verified = self.email_verified

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "user_type": user_type,
                "created_at": created_at,
                "last_login": last_login,
            }
        )
        if email is not UNSET:
            field_dict["email"] = email
        if email_verified is not UNSET:
            field_dict["email_verified"] = email_verified
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        user_type = UserType(d.pop("user_type"))

        created_at = d.pop("created_at")

        last_login = d.pop("last_login")

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        email_verified = d.pop("email_verified", UNSET)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        user = cls(
            user_id=user_id,
            user_type=user_type,
            created_at=created_at,
            last_login=last_login,
            email=email,
            email_verified=email_verified,
            name=name,
        )

        user.additional_properties = d
        return user

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

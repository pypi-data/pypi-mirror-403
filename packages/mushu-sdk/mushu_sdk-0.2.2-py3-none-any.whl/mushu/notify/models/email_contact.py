from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailContact")


@_attrs_define
class EmailContact:
    """Registered email contact.

    Attributes:
        email (str): Email address
        user_id (str): Associated user ID
        created_at (str): Registration timestamp
        subscribed (bool | Unset): Whether contact is subscribed Default: True.
    """

    email: str
    user_id: str
    created_at: str
    subscribed: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        user_id = self.user_id

        created_at = self.created_at

        subscribed = self.subscribed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "user_id": user_id,
                "created_at": created_at,
            }
        )
        if subscribed is not UNSET:
            field_dict["subscribed"] = subscribed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        user_id = d.pop("user_id")

        created_at = d.pop("created_at")

        subscribed = d.pop("subscribed", UNSET)

        email_contact = cls(
            email=email,
            user_id=user_id,
            created_at=created_at,
            subscribed=subscribed,
        )

        email_contact.additional_properties = d
        return email_contact

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

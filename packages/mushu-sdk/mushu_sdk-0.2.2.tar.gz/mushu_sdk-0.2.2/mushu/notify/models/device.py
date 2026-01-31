from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.platform import Platform
from ..types import UNSET, Unset

T = TypeVar("T", bound="Device")


@_attrs_define
class Device:
    """Registered device.

    Attributes:
        token (str): APNs device token
        user_id (str): Associated user ID
        platform (Platform): Device platform.
        created_at (str): Registration timestamp
        updated_at (str): Last update timestamp
        app_version (None | str | Unset): App version
    """

    token: str
    user_id: str
    platform: Platform
    created_at: str
    updated_at: str
    app_version: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        token = self.token

        user_id = self.user_id

        platform = self.platform.value

        created_at = self.created_at

        updated_at = self.updated_at

        app_version: None | str | Unset
        if isinstance(self.app_version, Unset):
            app_version = UNSET
        else:
            app_version = self.app_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "token": token,
                "user_id": user_id,
                "platform": platform,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if app_version is not UNSET:
            field_dict["app_version"] = app_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        token = d.pop("token")

        user_id = d.pop("user_id")

        platform = Platform(d.pop("platform"))

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        def _parse_app_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_version = _parse_app_version(d.pop("app_version", UNSET))

        device = cls(
            token=token,
            user_id=user_id,
            platform=platform,
            created_at=created_at,
            updated_at=updated_at,
            app_version=app_version,
        )

        device.additional_properties = d
        return device

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

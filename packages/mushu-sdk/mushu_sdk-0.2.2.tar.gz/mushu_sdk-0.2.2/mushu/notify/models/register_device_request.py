from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.platform import Platform
from ..types import UNSET, Unset

T = TypeVar("T", bound="RegisterDeviceRequest")


@_attrs_define
class RegisterDeviceRequest:
    """Request to register a device.

    Attributes:
        user_id (str): User ID to associate device with
        token (str): APNs device token
        platform (Platform): Device platform.
        app_version (None | str | Unset): App version
    """

    user_id: str
    token: str
    platform: Platform
    app_version: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        token = self.token

        platform = self.platform.value

        app_version: None | str | Unset
        if isinstance(self.app_version, Unset):
            app_version = UNSET
        else:
            app_version = self.app_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "token": token,
                "platform": platform,
            }
        )
        if app_version is not UNSET:
            field_dict["app_version"] = app_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        token = d.pop("token")

        platform = Platform(d.pop("platform"))

        def _parse_app_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_version = _parse_app_version(d.pop("app_version", UNSET))

        register_device_request = cls(
            user_id=user_id,
            token=token,
            platform=platform,
            app_version=app_version,
        )

        register_device_request.additional_properties = d
        return register_device_request

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

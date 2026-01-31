from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAppRequest")


@_attrs_define
class CreateAppRequest:
    """Request to create an app.

    Attributes:
        name (str): App name
        bundle_id (str): iOS bundle ID
        android_package (None | str | Unset): Android package name
    """

    name: str
    bundle_id: str
    android_package: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        bundle_id = self.bundle_id

        android_package: None | str | Unset
        if isinstance(self.android_package, Unset):
            android_package = UNSET
        else:
            android_package = self.android_package

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "bundle_id": bundle_id,
            }
        )
        if android_package is not UNSET:
            field_dict["android_package"] = android_package

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        bundle_id = d.pop("bundle_id")

        def _parse_android_package(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        android_package = _parse_android_package(d.pop("android_package", UNSET))

        create_app_request = cls(
            name=name,
            bundle_id=bundle_id,
            android_package=android_package,
        )

        create_app_request.additional_properties = d
        return create_app_request

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

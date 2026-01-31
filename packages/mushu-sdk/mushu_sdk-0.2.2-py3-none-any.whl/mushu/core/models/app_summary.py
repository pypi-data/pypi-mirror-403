from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AppSummary")


@_attrs_define
class AppSummary:
    """Summary of an app (without full key details).

    Attributes:
        app_id (str): Unique app ID
        org_id (str): Parent organization ID
        name (str): App name
        bundle_id (str): iOS bundle ID
        created_at (str): Creation timestamp
        android_package (None | str | Unset): Android package name
    """

    app_id: str
    org_id: str
    name: str
    bundle_id: str
    created_at: str
    android_package: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        org_id = self.org_id

        name = self.name

        bundle_id = self.bundle_id

        created_at = self.created_at

        android_package: None | str | Unset
        if isinstance(self.android_package, Unset):
            android_package = UNSET
        else:
            android_package = self.android_package

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "org_id": org_id,
                "name": name,
                "bundle_id": bundle_id,
                "created_at": created_at,
            }
        )
        if android_package is not UNSET:
            field_dict["android_package"] = android_package

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_id = d.pop("app_id")

        org_id = d.pop("org_id")

        name = d.pop("name")

        bundle_id = d.pop("bundle_id")

        created_at = d.pop("created_at")

        def _parse_android_package(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        android_package = _parse_android_package(d.pop("android_package", UNSET))

        app_summary = cls(
            app_id=app_id,
            org_id=org_id,
            name=name,
            bundle_id=bundle_id,
            created_at=created_at,
            android_package=android_package,
        )

        app_summary.additional_properties = d
        return app_summary

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

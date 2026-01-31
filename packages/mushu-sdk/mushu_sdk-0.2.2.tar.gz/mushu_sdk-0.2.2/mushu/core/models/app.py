from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="App")


@_attrs_define
class App:
    """Application belonging to an organization.

    Attributes:
        app_id (str): Unique app ID (app_xxxxxxxx)
        org_id (str): Parent organization ID
        name (str): App name (e.g., 'My iOS App')
        bundle_id (str): iOS bundle ID (e.g., 'com.mycompany.myapp')
        created_at (str): Creation timestamp
        created_by (str): User ID who created the app
        public_key (str): PEM-encoded public key
        key_algorithm (str): Key algorithm (ES256 or RS256)
        key_id (str): Key identifier for rotation
        key_created_at (str): When the key was created
        android_package (None | str | Unset): Android package name (future)
    """

    app_id: str
    org_id: str
    name: str
    bundle_id: str
    created_at: str
    created_by: str
    public_key: str
    key_algorithm: str
    key_id: str
    key_created_at: str
    android_package: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        org_id = self.org_id

        name = self.name

        bundle_id = self.bundle_id

        created_at = self.created_at

        created_by = self.created_by

        public_key = self.public_key

        key_algorithm = self.key_algorithm

        key_id = self.key_id

        key_created_at = self.key_created_at

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
                "created_by": created_by,
                "public_key": public_key,
                "key_algorithm": key_algorithm,
                "key_id": key_id,
                "key_created_at": key_created_at,
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

        created_by = d.pop("created_by")

        public_key = d.pop("public_key")

        key_algorithm = d.pop("key_algorithm")

        key_id = d.pop("key_id")

        key_created_at = d.pop("key_created_at")

        def _parse_android_package(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        android_package = _parse_android_package(d.pop("android_package", UNSET))

        app = cls(
            app_id=app_id,
            org_id=org_id,
            name=name,
            bundle_id=bundle_id,
            created_at=created_at,
            created_by=created_by,
            public_key=public_key,
            key_algorithm=key_algorithm,
            key_id=key_id,
            key_created_at=key_created_at,
            android_package=android_package,
        )

        app.additional_properties = d
        return app

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RotateKeysResponse")


@_attrs_define
class RotateKeysResponse:
    """Response after rotating app keys.

    Attributes:
        app_id (str): App ID
        key_id (str): New key identifier
        algorithm (str): Key algorithm
        public_key (str): New PEM-encoded public key
    """

    app_id: str
    key_id: str
    algorithm: str
    public_key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        key_id = self.key_id

        algorithm = self.algorithm

        public_key = self.public_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "key_id": key_id,
                "algorithm": algorithm,
                "public_key": public_key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_id = d.pop("app_id")

        key_id = d.pop("key_id")

        algorithm = d.pop("algorithm")

        public_key = d.pop("public_key")

        rotate_keys_response = cls(
            app_id=app_id,
            key_id=key_id,
            algorithm=algorithm,
            public_key=public_key,
        )

        rotate_keys_response.additional_properties = d
        return rotate_keys_response

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

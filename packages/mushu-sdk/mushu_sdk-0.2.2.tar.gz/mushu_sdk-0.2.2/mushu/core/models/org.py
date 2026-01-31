from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Org")


@_attrs_define
class Org:
    """Organization.

    Attributes:
        org_id (str): Unique organization ID (org_xxxxxxxx)
        name (str): Organization name
        created_at (str): Creation timestamp
        created_by (str): User ID who created the org
    """

    org_id: str
    name: str
    created_at: str
    created_by: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        name = self.name

        created_at = self.created_at

        created_by = self.created_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "name": name,
                "created_at": created_at,
                "created_by": created_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("org_id")

        name = d.pop("name")

        created_at = d.pop("created_at")

        created_by = d.pop("created_by")

        org = cls(
            org_id=org_id,
            name=name,
            created_at=created_at,
            created_by=created_by,
        )

        org.additional_properties = d
        return org

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

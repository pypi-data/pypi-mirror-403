from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="AppConfig")


@_attrs_define
class AppConfig:
    """App leaderboards config response model.

    Attributes:
        app_id (str):
        org_id (str):
        created_at (datetime.datetime):
        created_by (str):
    """

    app_id: str
    org_id: str
    created_at: datetime.datetime
    created_by: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        org_id = self.org_id

        created_at = self.created_at.isoformat()

        created_by = self.created_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "org_id": org_id,
                "created_at": created_at,
                "created_by": created_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_id = d.pop("app_id")

        org_id = d.pop("org_id")

        created_at = isoparse(d.pop("created_at"))

        created_by = d.pop("created_by")

        app_config = cls(
            app_id=app_id,
            org_id=org_id,
            created_at=created_at,
            created_by=created_by,
        )

        app_config.additional_properties = d
        return app_config

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

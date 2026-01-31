from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StreaksConfig")


@_attrs_define
class StreaksConfig:
    """App-specific streak configuration.

    Attributes:
        grace_period_days (int | Unset): Number of days a user can miss without breaking streak Default: 0.
        activity_types (list[str] | Unset): Allowed activity types (empty = all allowed)
    """

    grace_period_days: int | Unset = 0
    activity_types: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        grace_period_days = self.grace_period_days

        activity_types: list[str] | Unset = UNSET
        if not isinstance(self.activity_types, Unset):
            activity_types = self.activity_types

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if grace_period_days is not UNSET:
            field_dict["grace_period_days"] = grace_period_days
        if activity_types is not UNSET:
            field_dict["activity_types"] = activity_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        grace_period_days = d.pop("grace_period_days", UNSET)

        activity_types = cast(list[str], d.pop("activity_types", UNSET))

        streaks_config = cls(
            grace_period_days=grace_period_days,
            activity_types=activity_types,
        )

        streaks_config.additional_properties = d
        return streaks_config

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

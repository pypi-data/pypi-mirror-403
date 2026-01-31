from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ConfigureStreaksRequest")


@_attrs_define
class ConfigureStreaksRequest:
    """Request to configure app streak settings.

    Attributes:
        grace_period_days (int | None | Unset): Number of days a user can miss without breaking streak
        activity_types (list[str] | None | Unset): Allowed activity types (empty = all allowed)
    """

    grace_period_days: int | None | Unset = UNSET
    activity_types: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        grace_period_days: int | None | Unset
        if isinstance(self.grace_period_days, Unset):
            grace_period_days = UNSET
        else:
            grace_period_days = self.grace_period_days

        activity_types: list[str] | None | Unset
        if isinstance(self.activity_types, Unset):
            activity_types = UNSET
        elif isinstance(self.activity_types, list):
            activity_types = self.activity_types

        else:
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

        def _parse_grace_period_days(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        grace_period_days = _parse_grace_period_days(d.pop("grace_period_days", UNSET))

        def _parse_activity_types(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                activity_types_type_0 = cast(list[str], data)

                return activity_types_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        activity_types = _parse_activity_types(d.pop("activity_types", UNSET))

        configure_streaks_request = cls(
            grace_period_days=grace_period_days,
            activity_types=activity_types,
        )

        configure_streaks_request.additional_properties = d
        return configure_streaks_request

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

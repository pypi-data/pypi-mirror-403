from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AntiCheatConfig")


@_attrs_define
class AntiCheatConfig:
    """Anti-cheat configuration for a board.

    Attributes:
        max_score_per_entry (float | None | Unset): Maximum score allowed per entry
        max_entries_per_day (int | None | Unset): Maximum entries per user per day
        min_interval_seconds (int | None | Unset): Minimum seconds between entries
    """

    max_score_per_entry: float | None | Unset = UNSET
    max_entries_per_day: int | None | Unset = UNSET
    min_interval_seconds: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        max_score_per_entry: float | None | Unset
        if isinstance(self.max_score_per_entry, Unset):
            max_score_per_entry = UNSET
        else:
            max_score_per_entry = self.max_score_per_entry

        max_entries_per_day: int | None | Unset
        if isinstance(self.max_entries_per_day, Unset):
            max_entries_per_day = UNSET
        else:
            max_entries_per_day = self.max_entries_per_day

        min_interval_seconds: int | None | Unset
        if isinstance(self.min_interval_seconds, Unset):
            min_interval_seconds = UNSET
        else:
            min_interval_seconds = self.min_interval_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if max_score_per_entry is not UNSET:
            field_dict["max_score_per_entry"] = max_score_per_entry
        if max_entries_per_day is not UNSET:
            field_dict["max_entries_per_day"] = max_entries_per_day
        if min_interval_seconds is not UNSET:
            field_dict["min_interval_seconds"] = min_interval_seconds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_max_score_per_entry(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        max_score_per_entry = _parse_max_score_per_entry(d.pop("max_score_per_entry", UNSET))

        def _parse_max_entries_per_day(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_entries_per_day = _parse_max_entries_per_day(d.pop("max_entries_per_day", UNSET))

        def _parse_min_interval_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        min_interval_seconds = _parse_min_interval_seconds(d.pop("min_interval_seconds", UNSET))

        anti_cheat_config = cls(
            max_score_per_entry=max_score_per_entry,
            max_entries_per_day=max_entries_per_day,
            min_interval_seconds=min_interval_seconds,
        )

        anti_cheat_config.additional_properties = d
        return anti_cheat_config

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RecordActivityResponse")


@_attrs_define
class RecordActivityResponse:
    """Response after recording an activity.

    Attributes:
        activity_id (str):
        current_streak (int):
        longest_streak (int):
        total_count (int):
        streak_extended (bool): True if this activity extended an existing streak
        streak_started (bool): True if this activity started a new streak
    """

    activity_id: str
    current_streak: int
    longest_streak: int
    total_count: int
    streak_extended: bool
    streak_started: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        activity_id = self.activity_id

        current_streak = self.current_streak

        longest_streak = self.longest_streak

        total_count = self.total_count

        streak_extended = self.streak_extended

        streak_started = self.streak_started

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "activity_id": activity_id,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "total_count": total_count,
                "streak_extended": streak_extended,
                "streak_started": streak_started,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        activity_id = d.pop("activity_id")

        current_streak = d.pop("current_streak")

        longest_streak = d.pop("longest_streak")

        total_count = d.pop("total_count")

        streak_extended = d.pop("streak_extended")

        streak_started = d.pop("streak_started")

        record_activity_response = cls(
            activity_id=activity_id,
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_count=total_count,
            streak_extended=streak_extended,
            streak_started=streak_started,
        )

        record_activity_response.additional_properties = d
        return record_activity_response

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

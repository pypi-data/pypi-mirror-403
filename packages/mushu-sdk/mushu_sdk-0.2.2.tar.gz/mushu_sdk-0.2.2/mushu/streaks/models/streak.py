from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="Streak")


@_attrs_define
class Streak:
    """User's streak information for an activity type.

    Attributes:
        user_id (str):
        activity_type (str):
        current_streak (int):
        longest_streak (int):
        total_count (int):
        last_activity_date (str): YYYY-MM-DD in user's timezone
        last_activity_at (datetime.datetime):
    """

    user_id: str
    activity_type: str
    current_streak: int
    longest_streak: int
    total_count: int
    last_activity_date: str
    last_activity_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        activity_type = self.activity_type

        current_streak = self.current_streak

        longest_streak = self.longest_streak

        total_count = self.total_count

        last_activity_date = self.last_activity_date

        last_activity_at = self.last_activity_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "activity_type": activity_type,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "total_count": total_count,
                "last_activity_date": last_activity_date,
                "last_activity_at": last_activity_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        activity_type = d.pop("activity_type")

        current_streak = d.pop("current_streak")

        longest_streak = d.pop("longest_streak")

        total_count = d.pop("total_count")

        last_activity_date = d.pop("last_activity_date")

        last_activity_at = isoparse(d.pop("last_activity_at"))

        streak = cls(
            user_id=user_id,
            activity_type=activity_type,
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_count=total_count,
            last_activity_date=last_activity_date,
            last_activity_at=last_activity_at,
        )

        streak.additional_properties = d
        return streak

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

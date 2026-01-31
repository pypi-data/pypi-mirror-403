from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.streak_activity import StreakActivity


T = TypeVar("T", bound="StreakHistory")


@_attrs_define
class StreakHistory:
    """User's activity history.

    Attributes:
        user_id (str):
        activities (list[StreakActivity]):
        total_count (int):
    """

    user_id: str
    activities: list[StreakActivity]
    total_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        activities = []
        for activities_item_data in self.activities:
            activities_item = activities_item_data.to_dict()
            activities.append(activities_item)

        total_count = self.total_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "activities": activities,
                "total_count": total_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.streak_activity import StreakActivity

        d = dict(src_dict)
        user_id = d.pop("user_id")

        activities = []
        _activities = d.pop("activities")
        for activities_item_data in _activities:
            activities_item = StreakActivity.from_dict(activities_item_data)

            activities.append(activities_item)

        total_count = d.pop("total_count")

        streak_history = cls(
            user_id=user_id,
            activities=activities,
            total_count=total_count,
        )

        streak_history.additional_properties = d
        return streak_history

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

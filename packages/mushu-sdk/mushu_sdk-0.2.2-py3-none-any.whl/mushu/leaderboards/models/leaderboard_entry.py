from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="LeaderboardEntry")


@_attrs_define
class LeaderboardEntry:
    """Single entry in a leaderboard.

    Attributes:
        rank (int):
        user_id (str):
        score (float):
        entry_count (int): Number of score submissions
        last_updated (datetime.datetime):
    """

    rank: int
    user_id: str
    score: float
    entry_count: int
    last_updated: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rank = self.rank

        user_id = self.user_id

        score = self.score

        entry_count = self.entry_count

        last_updated = self.last_updated.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "rank": rank,
                "user_id": user_id,
                "score": score,
                "entry_count": entry_count,
                "last_updated": last_updated,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rank = d.pop("rank")

        user_id = d.pop("user_id")

        score = d.pop("score")

        entry_count = d.pop("entry_count")

        last_updated = isoparse(d.pop("last_updated"))

        leaderboard_entry = cls(
            rank=rank,
            user_id=user_id,
            score=score,
            entry_count=entry_count,
            last_updated=last_updated,
        )

        leaderboard_entry.additional_properties = d
        return leaderboard_entry

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

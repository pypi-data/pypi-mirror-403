from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.time_window import TimeWindow
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.leaderboard_entry import LeaderboardEntry


T = TypeVar("T", bound="LeaderboardResponse")


@_attrs_define
class LeaderboardResponse:
    """Response for leaderboard query.

    Attributes:
        board_id (str):
        time_window (TimeWindow): Time window for leaderboard aggregation.
        entries (list[LeaderboardEntry]):
        total_users (int):
        cached_at (datetime.datetime | None | Unset): When the cached result was generated
    """

    board_id: str
    time_window: TimeWindow
    entries: list[LeaderboardEntry]
    total_users: int
    cached_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        board_id = self.board_id

        time_window = self.time_window.value

        entries = []
        for entries_item_data in self.entries:
            entries_item = entries_item_data.to_dict()
            entries.append(entries_item)

        total_users = self.total_users

        cached_at: None | str | Unset
        if isinstance(self.cached_at, Unset):
            cached_at = UNSET
        elif isinstance(self.cached_at, datetime.datetime):
            cached_at = self.cached_at.isoformat()
        else:
            cached_at = self.cached_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "board_id": board_id,
                "time_window": time_window,
                "entries": entries,
                "total_users": total_users,
            }
        )
        if cached_at is not UNSET:
            field_dict["cached_at"] = cached_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.leaderboard_entry import LeaderboardEntry

        d = dict(src_dict)
        board_id = d.pop("board_id")

        time_window = TimeWindow(d.pop("time_window"))

        entries = []
        _entries = d.pop("entries")
        for entries_item_data in _entries:
            entries_item = LeaderboardEntry.from_dict(entries_item_data)

            entries.append(entries_item)

        total_users = d.pop("total_users")

        def _parse_cached_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                cached_at_type_0 = isoparse(data)

                return cached_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        cached_at = _parse_cached_at(d.pop("cached_at", UNSET))

        leaderboard_response = cls(
            board_id=board_id,
            time_window=time_window,
            entries=entries,
            total_users=total_users,
            cached_at=cached_at,
        )

        leaderboard_response.additional_properties = d
        return leaderboard_response

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

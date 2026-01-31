from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.time_window import TimeWindow

T = TypeVar("T", bound="RankResponse")


@_attrs_define
class RankResponse:
    """Response for rank query.

    Attributes:
        board_id (str):
        time_window (TimeWindow): Time window for leaderboard aggregation.
        user_id (str):
        rank (int):
        score (float):
        percentile (float): User's percentile (0-100, 100 = top)
        total_users (int):
    """

    board_id: str
    time_window: TimeWindow
    user_id: str
    rank: int
    score: float
    percentile: float
    total_users: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        board_id = self.board_id

        time_window = self.time_window.value

        user_id = self.user_id

        rank = self.rank

        score = self.score

        percentile = self.percentile

        total_users = self.total_users

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "board_id": board_id,
                "time_window": time_window,
                "user_id": user_id,
                "rank": rank,
                "score": score,
                "percentile": percentile,
                "total_users": total_users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        board_id = d.pop("board_id")

        time_window = TimeWindow(d.pop("time_window"))

        user_id = d.pop("user_id")

        rank = d.pop("rank")

        score = d.pop("score")

        percentile = d.pop("percentile")

        total_users = d.pop("total_users")

        rank_response = cls(
            board_id=board_id,
            time_window=time_window,
            user_id=user_id,
            rank=rank,
            score=score,
            percentile=percentile,
            total_users=total_users,
        )

        rank_response.additional_properties = d
        return rank_response

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

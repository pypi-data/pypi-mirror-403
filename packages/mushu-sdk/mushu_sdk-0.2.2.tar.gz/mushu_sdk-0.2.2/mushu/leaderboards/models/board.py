from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.aggregation import Aggregation
from ..models.time_window import TimeWindow

if TYPE_CHECKING:
    from ..models.anti_cheat_config import AntiCheatConfig


T = TypeVar("T", bound="Board")


@_attrs_define
class Board:
    """Board response model.

    Attributes:
        board_id (str):
        app_id (str):
        name (str):
        metric (str):
        aggregation (Aggregation): Score aggregation method.
        time_windows (list[TimeWindow]):
        anti_cheat (AntiCheatConfig | None):
        created_at (datetime.datetime):
    """

    board_id: str
    app_id: str
    name: str
    metric: str
    aggregation: Aggregation
    time_windows: list[TimeWindow]
    anti_cheat: AntiCheatConfig | None
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.anti_cheat_config import AntiCheatConfig

        board_id = self.board_id

        app_id = self.app_id

        name = self.name

        metric = self.metric

        aggregation = self.aggregation.value

        time_windows = []
        for time_windows_item_data in self.time_windows:
            time_windows_item = time_windows_item_data.value
            time_windows.append(time_windows_item)

        anti_cheat: dict[str, Any] | None
        if isinstance(self.anti_cheat, AntiCheatConfig):
            anti_cheat = self.anti_cheat.to_dict()
        else:
            anti_cheat = self.anti_cheat

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "board_id": board_id,
                "app_id": app_id,
                "name": name,
                "metric": metric,
                "aggregation": aggregation,
                "time_windows": time_windows,
                "anti_cheat": anti_cheat,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.anti_cheat_config import AntiCheatConfig

        d = dict(src_dict)
        board_id = d.pop("board_id")

        app_id = d.pop("app_id")

        name = d.pop("name")

        metric = d.pop("metric")

        aggregation = Aggregation(d.pop("aggregation"))

        time_windows = []
        _time_windows = d.pop("time_windows")
        for time_windows_item_data in _time_windows:
            time_windows_item = TimeWindow(time_windows_item_data)

            time_windows.append(time_windows_item)

        def _parse_anti_cheat(data: object) -> AntiCheatConfig | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                anti_cheat_type_0 = AntiCheatConfig.from_dict(data)

                return anti_cheat_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AntiCheatConfig | None, data)

        anti_cheat = _parse_anti_cheat(d.pop("anti_cheat"))

        created_at = isoparse(d.pop("created_at"))

        board = cls(
            board_id=board_id,
            app_id=app_id,
            name=name,
            metric=metric,
            aggregation=aggregation,
            time_windows=time_windows,
            anti_cheat=anti_cheat,
            created_at=created_at,
        )

        board.additional_properties = d
        return board

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

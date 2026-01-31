from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.aggregation import Aggregation
from ..models.time_window import TimeWindow
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.anti_cheat_config import AntiCheatConfig


T = TypeVar("T", bound="CreateBoardRequest")


@_attrs_define
class CreateBoardRequest:
    """Request to create a leaderboard.

    Attributes:
        board_id (str): Board identifier
        name (str): Human-readable board name
        metric (str | Unset): Metric name Default: 'score'.
        aggregation (Aggregation | Unset): Score aggregation method.
        time_windows (list[TimeWindow] | Unset): Enabled time windows
        anti_cheat (AntiCheatConfig | None | Unset): Anti-cheat settings
    """

    board_id: str
    name: str
    metric: str | Unset = "score"
    aggregation: Aggregation | Unset = UNSET
    time_windows: list[TimeWindow] | Unset = UNSET
    anti_cheat: AntiCheatConfig | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.anti_cheat_config import AntiCheatConfig

        board_id = self.board_id

        name = self.name

        metric = self.metric

        aggregation: str | Unset = UNSET
        if not isinstance(self.aggregation, Unset):
            aggregation = self.aggregation.value

        time_windows: list[str] | Unset = UNSET
        if not isinstance(self.time_windows, Unset):
            time_windows = []
            for time_windows_item_data in self.time_windows:
                time_windows_item = time_windows_item_data.value
                time_windows.append(time_windows_item)

        anti_cheat: dict[str, Any] | None | Unset
        if isinstance(self.anti_cheat, Unset):
            anti_cheat = UNSET
        elif isinstance(self.anti_cheat, AntiCheatConfig):
            anti_cheat = self.anti_cheat.to_dict()
        else:
            anti_cheat = self.anti_cheat

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "board_id": board_id,
                "name": name,
            }
        )
        if metric is not UNSET:
            field_dict["metric"] = metric
        if aggregation is not UNSET:
            field_dict["aggregation"] = aggregation
        if time_windows is not UNSET:
            field_dict["time_windows"] = time_windows
        if anti_cheat is not UNSET:
            field_dict["anti_cheat"] = anti_cheat

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.anti_cheat_config import AntiCheatConfig

        d = dict(src_dict)
        board_id = d.pop("board_id")

        name = d.pop("name")

        metric = d.pop("metric", UNSET)

        _aggregation = d.pop("aggregation", UNSET)
        aggregation: Aggregation | Unset
        if isinstance(_aggregation, Unset):
            aggregation = UNSET
        else:
            aggregation = Aggregation(_aggregation)

        _time_windows = d.pop("time_windows", UNSET)
        time_windows: list[TimeWindow] | Unset = UNSET
        if _time_windows is not UNSET:
            time_windows = []
            for time_windows_item_data in _time_windows:
                time_windows_item = TimeWindow(time_windows_item_data)

                time_windows.append(time_windows_item)

        def _parse_anti_cheat(data: object) -> AntiCheatConfig | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                anti_cheat_type_0 = AntiCheatConfig.from_dict(data)

                return anti_cheat_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AntiCheatConfig | None | Unset, data)

        anti_cheat = _parse_anti_cheat(d.pop("anti_cheat", UNSET))

        create_board_request = cls(
            board_id=board_id,
            name=name,
            metric=metric,
            aggregation=aggregation,
            time_windows=time_windows,
            anti_cheat=anti_cheat,
        )

        create_board_request.additional_properties = d
        return create_board_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.daily_stats import DailyStats


T = TypeVar("T", bound="TimeSeriesResponse")


@_attrs_define
class TimeSeriesResponse:
    """Time series analytics response.

    Attributes:
        app_id (str):
        start_date (str):
        end_date (str):
        daily (list[DailyStats]):
    """

    app_id: str
    start_date: str
    end_date: str
    daily: list[DailyStats]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        start_date = self.start_date

        end_date = self.end_date

        daily = []
        for daily_item_data in self.daily:
            daily_item = daily_item_data.to_dict()
            daily.append(daily_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "start_date": start_date,
                "end_date": end_date,
                "daily": daily,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.daily_stats import DailyStats

        d = dict(src_dict)
        app_id = d.pop("app_id")

        start_date = d.pop("start_date")

        end_date = d.pop("end_date")

        daily = []
        _daily = d.pop("daily")
        for daily_item_data in _daily:
            daily_item = DailyStats.from_dict(daily_item_data)

            daily.append(daily_item)

        time_series_response = cls(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            daily=daily,
        )

        time_series_response.additional_properties = d
        return time_series_response

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

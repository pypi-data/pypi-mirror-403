from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.channel_stats import ChannelStats


T = TypeVar("T", bound="AnalyticsResponse")


@_attrs_define
class AnalyticsResponse:
    """Analytics response model.

    Attributes:
        app_id (str):
        start_date (str):
        end_date (str):
        total_events (int):
        push (ChannelStats): Stats for a single channel.
        email (ChannelStats): Stats for a single channel.
    """

    app_id: str
    start_date: str
    end_date: str
    total_events: int
    push: ChannelStats
    email: ChannelStats
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        start_date = self.start_date

        end_date = self.end_date

        total_events = self.total_events

        push = self.push.to_dict()

        email = self.email.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_events": total_events,
                "push": push,
                "email": email,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.channel_stats import ChannelStats

        d = dict(src_dict)
        app_id = d.pop("app_id")

        start_date = d.pop("start_date")

        end_date = d.pop("end_date")

        total_events = d.pop("total_events")

        push = ChannelStats.from_dict(d.pop("push"))

        email = ChannelStats.from_dict(d.pop("email"))

        analytics_response = cls(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            total_events=total_events,
            push=push,
            email=email,
        )

        analytics_response.additional_properties = d
        return analytics_response

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

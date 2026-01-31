from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DailyStats")


@_attrs_define
class DailyStats:
    """Daily stats for time series.

    Attributes:
        date (str):
        push_sent (int):
        push_delivered (int):
        push_failed (int):
        email_sent (int):
        email_delivered (int):
        email_failed (int):
    """

    date: str
    push_sent: int
    push_delivered: int
    push_failed: int
    email_sent: int
    email_delivered: int
    email_failed: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        date = self.date

        push_sent = self.push_sent

        push_delivered = self.push_delivered

        push_failed = self.push_failed

        email_sent = self.email_sent

        email_delivered = self.email_delivered

        email_failed = self.email_failed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "date": date,
                "push_sent": push_sent,
                "push_delivered": push_delivered,
                "push_failed": push_failed,
                "email_sent": email_sent,
                "email_delivered": email_delivered,
                "email_failed": email_failed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        date = d.pop("date")

        push_sent = d.pop("push_sent")

        push_delivered = d.pop("push_delivered")

        push_failed = d.pop("push_failed")

        email_sent = d.pop("email_sent")

        email_delivered = d.pop("email_delivered")

        email_failed = d.pop("email_failed")

        daily_stats = cls(
            date=date,
            push_sent=push_sent,
            push_delivered=push_delivered,
            push_failed=push_failed,
            email_sent=email_sent,
            email_delivered=email_delivered,
            email_failed=email_failed,
        )

        daily_stats.additional_properties = d
        return daily_stats

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

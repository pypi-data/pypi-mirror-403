from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ChannelStats")


@_attrs_define
class ChannelStats:
    """Stats for a single channel.

    Attributes:
        sent (int):
        delivered (int):
        failed (int):
        delivery_rate (float):
    """

    sent: int
    delivered: int
    failed: int
    delivery_rate: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sent = self.sent

        delivered = self.delivered

        failed = self.failed

        delivery_rate = self.delivery_rate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sent": sent,
                "delivered": delivered,
                "failed": failed,
                "delivery_rate": delivery_rate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sent = d.pop("sent")

        delivered = d.pop("delivered")

        failed = d.pop("failed")

        delivery_rate = d.pop("delivery_rate")

        channel_stats = cls(
            sent=sent,
            delivered=delivered,
            failed=failed,
            delivery_rate=delivery_rate,
        )

        channel_stats.additional_properties = d
        return channel_stats

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="QuotaUsage")


@_attrs_define
class QuotaUsage:
    """Current usage against a quota limit.

    Attributes:
        service (str):
        metric (str):
        limit (int):
        current (int):
        remaining (int):
        percentage (str):
        period (str):
        exceeded (bool):
        warning (bool):
    """

    service: str
    metric: str
    limit: int
    current: int
    remaining: int
    percentage: str
    period: str
    exceeded: bool
    warning: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service = self.service

        metric = self.metric

        limit = self.limit

        current = self.current

        remaining = self.remaining

        percentage = self.percentage

        period = self.period

        exceeded = self.exceeded

        warning = self.warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "service": service,
                "metric": metric,
                "limit": limit,
                "current": current,
                "remaining": remaining,
                "percentage": percentage,
                "period": period,
                "exceeded": exceeded,
                "warning": warning,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        service = d.pop("service")

        metric = d.pop("metric")

        limit = d.pop("limit")

        current = d.pop("current")

        remaining = d.pop("remaining")

        percentage = d.pop("percentage")

        period = d.pop("period")

        exceeded = d.pop("exceeded")

        warning = d.pop("warning")

        quota_usage = cls(
            service=service,
            metric=metric,
            limit=limit,
            current=current,
            remaining=remaining,
            percentage=percentage,
            period=period,
            exceeded=exceeded,
            warning=warning,
        )

        quota_usage.additional_properties = d
        return quota_usage

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

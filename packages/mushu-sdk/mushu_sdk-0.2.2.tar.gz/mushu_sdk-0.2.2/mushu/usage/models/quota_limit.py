from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QuotaLimit")


@_attrs_define
class QuotaLimit:
    """A single quota limit configuration.

    Attributes:
        service (str):
        metric (str):
        limit (int):
        period (str | Unset):  Default: 'monthly'.
        warning_threshold (float | str | Unset):  Default: 0.8.
    """

    service: str
    metric: str
    limit: int
    period: str | Unset = "monthly"
    warning_threshold: float | str | Unset = 0.8
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        service = self.service

        metric = self.metric

        limit = self.limit

        period = self.period

        warning_threshold: float | str | Unset
        if isinstance(self.warning_threshold, Unset):
            warning_threshold = UNSET
        else:
            warning_threshold = self.warning_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "service": service,
                "metric": metric,
                "limit": limit,
            }
        )
        if period is not UNSET:
            field_dict["period"] = period
        if warning_threshold is not UNSET:
            field_dict["warning_threshold"] = warning_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        service = d.pop("service")

        metric = d.pop("metric")

        limit = d.pop("limit")

        period = d.pop("period", UNSET)

        def _parse_warning_threshold(data: object) -> float | str | Unset:
            if isinstance(data, Unset):
                return data
            return cast(float | str | Unset, data)

        warning_threshold = _parse_warning_threshold(d.pop("warning_threshold", UNSET))

        quota_limit = cls(
            service=service,
            metric=metric,
            limit=limit,
            period=period,
            warning_threshold=warning_threshold,
        )

        quota_limit.additional_properties = d
        return quota_limit

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

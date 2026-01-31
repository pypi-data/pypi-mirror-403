from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.usage_summary_by_app import UsageSummaryByApp


T = TypeVar("T", bound="UsageSummary")


@_attrs_define
class UsageSummary:
    """Aggregated usage summary for a period.

    Attributes:
        org_id (str):
        period (str):
        service (str):
        metric (str):
        total (int):
        by_app (UsageSummaryByApp | Unset):
    """

    org_id: str
    period: str
    service: str
    metric: str
    total: int
    by_app: UsageSummaryByApp | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        period = self.period

        service = self.service

        metric = self.metric

        total = self.total

        by_app: dict[str, Any] | Unset = UNSET
        if not isinstance(self.by_app, Unset):
            by_app = self.by_app.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "period": period,
                "service": service,
                "metric": metric,
                "total": total,
            }
        )
        if by_app is not UNSET:
            field_dict["by_app"] = by_app

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_summary_by_app import UsageSummaryByApp

        d = dict(src_dict)
        org_id = d.pop("org_id")

        period = d.pop("period")

        service = d.pop("service")

        metric = d.pop("metric")

        total = d.pop("total")

        _by_app = d.pop("by_app", UNSET)
        by_app: UsageSummaryByApp | Unset
        if isinstance(_by_app, Unset):
            by_app = UNSET
        else:
            by_app = UsageSummaryByApp.from_dict(_by_app)

        usage_summary = cls(
            org_id=org_id,
            period=period,
            service=service,
            metric=metric,
            total=total,
            by_app=by_app,
        )

        usage_summary.additional_properties = d
        return usage_summary

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

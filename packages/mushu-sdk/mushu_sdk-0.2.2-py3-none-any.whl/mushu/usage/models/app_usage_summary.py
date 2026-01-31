from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.app_usage_summary_total_by_service import AppUsageSummaryTotalByService
    from ..models.usage_summary import UsageSummary


T = TypeVar("T", bound="AppUsageSummary")


@_attrs_define
class AppUsageSummary:
    """Usage summary for an app.

    Attributes:
        app_id (str):
        org_id (str):
        period (str):
        summaries (list[UsageSummary]):
        total_by_service (AppUsageSummaryTotalByService):
    """

    app_id: str
    org_id: str
    period: str
    summaries: list[UsageSummary]
    total_by_service: AppUsageSummaryTotalByService
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        org_id = self.org_id

        period = self.period

        summaries = []
        for summaries_item_data in self.summaries:
            summaries_item = summaries_item_data.to_dict()
            summaries.append(summaries_item)

        total_by_service = self.total_by_service.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "org_id": org_id,
                "period": period,
                "summaries": summaries,
                "total_by_service": total_by_service,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_usage_summary_total_by_service import AppUsageSummaryTotalByService
        from ..models.usage_summary import UsageSummary

        d = dict(src_dict)
        app_id = d.pop("app_id")

        org_id = d.pop("org_id")

        period = d.pop("period")

        summaries = []
        _summaries = d.pop("summaries")
        for summaries_item_data in _summaries:
            summaries_item = UsageSummary.from_dict(summaries_item_data)

            summaries.append(summaries_item)

        total_by_service = AppUsageSummaryTotalByService.from_dict(d.pop("total_by_service"))

        app_usage_summary = cls(
            app_id=app_id,
            org_id=org_id,
            period=period,
            summaries=summaries,
            total_by_service=total_by_service,
        )

        app_usage_summary.additional_properties = d
        return app_usage_summary

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

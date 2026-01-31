from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.org_usage_summary_total_by_service import OrgUsageSummaryTotalByService
    from ..models.usage_summary import UsageSummary


T = TypeVar("T", bound="OrgUsageSummary")


@_attrs_define
class OrgUsageSummary:
    """Usage summary for an organization.

    Attributes:
        org_id (str):
        period (str):
        summaries (list[UsageSummary]):
        total_by_service (OrgUsageSummaryTotalByService):
    """

    org_id: str
    period: str
    summaries: list[UsageSummary]
    total_by_service: OrgUsageSummaryTotalByService
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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
                "org_id": org_id,
                "period": period,
                "summaries": summaries,
                "total_by_service": total_by_service,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.org_usage_summary_total_by_service import OrgUsageSummaryTotalByService
        from ..models.usage_summary import UsageSummary

        d = dict(src_dict)
        org_id = d.pop("org_id")

        period = d.pop("period")

        summaries = []
        _summaries = d.pop("summaries")
        for summaries_item_data in _summaries:
            summaries_item = UsageSummary.from_dict(summaries_item_data)

            summaries.append(summaries_item)

        total_by_service = OrgUsageSummaryTotalByService.from_dict(d.pop("total_by_service"))

        org_usage_summary = cls(
            org_id=org_id,
            period=period,
            summaries=summaries,
            total_by_service=total_by_service,
        )

        org_usage_summary.additional_properties = d
        return org_usage_summary

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

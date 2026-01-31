from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.quota_usage import QuotaUsage


T = TypeVar("T", bound="QuotaStatus")


@_attrs_define
class QuotaStatus:
    """Current quota status for an organization.

    Attributes:
        org_id (str):
        period (str):
        usages (list[QuotaUsage]):
        any_exceeded (bool):
        any_warning (bool):
    """

    org_id: str
    period: str
    usages: list[QuotaUsage]
    any_exceeded: bool
    any_warning: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        period = self.period

        usages = []
        for usages_item_data in self.usages:
            usages_item = usages_item_data.to_dict()
            usages.append(usages_item)

        any_exceeded = self.any_exceeded

        any_warning = self.any_warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "period": period,
                "usages": usages,
                "any_exceeded": any_exceeded,
                "any_warning": any_warning,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.quota_usage import QuotaUsage

        d = dict(src_dict)
        org_id = d.pop("org_id")

        period = d.pop("period")

        usages = []
        _usages = d.pop("usages")
        for usages_item_data in _usages:
            usages_item = QuotaUsage.from_dict(usages_item_data)

            usages.append(usages_item)

        any_exceeded = d.pop("any_exceeded")

        any_warning = d.pop("any_warning")

        quota_status = cls(
            org_id=org_id,
            period=period,
            usages=usages,
            any_exceeded=any_exceeded,
            any_warning=any_warning,
        )

        quota_status.additional_properties = d
        return quota_status

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

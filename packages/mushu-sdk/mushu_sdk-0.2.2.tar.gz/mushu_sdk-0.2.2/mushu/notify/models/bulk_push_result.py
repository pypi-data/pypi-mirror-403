from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.push_result import PushResult


T = TypeVar("T", bound="BulkPushResult")


@_attrs_define
class BulkPushResult:
    """Result of bulk push notification.

    Attributes:
        total (int): Total users targeted
        success (int): Successful sends
        failed (int): Failed sends
        results (list[PushResult]): Per-user results
    """

    total: int
    success: int
    failed: int
    results: list[PushResult]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        success = self.success

        failed = self.failed

        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "success": success,
                "failed": failed,
                "results": results,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.push_result import PushResult

        d = dict(src_dict)
        total = d.pop("total")

        success = d.pop("success")

        failed = d.pop("failed")

        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = PushResult.from_dict(results_item_data)

            results.append(results_item)

        bulk_push_result = cls(
            total=total,
            success=success,
            failed=failed,
            results=results,
        )

        bulk_push_result.additional_properties = d
        return bulk_push_result

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

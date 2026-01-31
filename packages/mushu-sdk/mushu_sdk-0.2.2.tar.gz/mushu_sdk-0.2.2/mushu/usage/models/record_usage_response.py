from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RecordUsageResponse")


@_attrs_define
class RecordUsageResponse:
    """Response after recording usage.

    Attributes:
        event_id (str):
        recorded (bool):
        quota_remaining (int | None | Unset):
        quota_warning (bool | Unset):  Default: False.
    """

    event_id: str
    recorded: bool
    quota_remaining: int | None | Unset = UNSET
    quota_warning: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_id = self.event_id

        recorded = self.recorded

        quota_remaining: int | None | Unset
        if isinstance(self.quota_remaining, Unset):
            quota_remaining = UNSET
        else:
            quota_remaining = self.quota_remaining

        quota_warning = self.quota_warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "event_id": event_id,
                "recorded": recorded,
            }
        )
        if quota_remaining is not UNSET:
            field_dict["quota_remaining"] = quota_remaining
        if quota_warning is not UNSET:
            field_dict["quota_warning"] = quota_warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        event_id = d.pop("event_id")

        recorded = d.pop("recorded")

        def _parse_quota_remaining(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        quota_remaining = _parse_quota_remaining(d.pop("quota_remaining", UNSET))

        quota_warning = d.pop("quota_warning", UNSET)

        record_usage_response = cls(
            event_id=event_id,
            recorded=recorded,
            quota_remaining=quota_remaining,
            quota_warning=quota_warning,
        )

        record_usage_response.additional_properties = d
        return record_usage_response

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

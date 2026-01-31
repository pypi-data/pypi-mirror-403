from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UsageCheckRequest")


@_attrs_define
class UsageCheckRequest:
    """Pre-check if operation is allowed under quota.

    Attributes:
        org_id (str):
        service (str):
        metric (str):
        quantity (int | Unset):  Default: 1.
    """

    org_id: str
    service: str
    metric: str
    quantity: int | Unset = 1
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        service = self.service

        metric = self.metric

        quantity = self.quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "service": service,
                "metric": metric,
            }
        )
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("org_id")

        service = d.pop("service")

        metric = d.pop("metric")

        quantity = d.pop("quantity", UNSET)

        usage_check_request = cls(
            org_id=org_id,
            service=service,
            metric=metric,
            quantity=quantity,
        )

        usage_check_request.additional_properties = d
        return usage_check_request

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

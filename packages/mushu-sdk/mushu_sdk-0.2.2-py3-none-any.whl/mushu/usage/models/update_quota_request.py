from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.quota_limit import QuotaLimit


T = TypeVar("T", bound="UpdateQuotaRequest")


@_attrs_define
class UpdateQuotaRequest:
    """Request to update quota configuration.

    Attributes:
        limits (list[QuotaLimit] | None | Unset):
        enforce_quotas (bool | None | Unset):
    """

    limits: list[QuotaLimit] | None | Unset = UNSET
    enforce_quotas: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        limits: list[dict[str, Any]] | None | Unset
        if isinstance(self.limits, Unset):
            limits = UNSET
        elif isinstance(self.limits, list):
            limits = []
            for limits_type_0_item_data in self.limits:
                limits_type_0_item = limits_type_0_item_data.to_dict()
                limits.append(limits_type_0_item)

        else:
            limits = self.limits

        enforce_quotas: bool | None | Unset
        if isinstance(self.enforce_quotas, Unset):
            enforce_quotas = UNSET
        else:
            enforce_quotas = self.enforce_quotas

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if limits is not UNSET:
            field_dict["limits"] = limits
        if enforce_quotas is not UNSET:
            field_dict["enforce_quotas"] = enforce_quotas

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.quota_limit import QuotaLimit

        d = dict(src_dict)

        def _parse_limits(data: object) -> list[QuotaLimit] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                limits_type_0 = []
                _limits_type_0 = data
                for limits_type_0_item_data in _limits_type_0:
                    limits_type_0_item = QuotaLimit.from_dict(limits_type_0_item_data)

                    limits_type_0.append(limits_type_0_item)

                return limits_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[QuotaLimit] | None | Unset, data)

        limits = _parse_limits(d.pop("limits", UNSET))

        def _parse_enforce_quotas(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        enforce_quotas = _parse_enforce_quotas(d.pop("enforce_quotas", UNSET))

        update_quota_request = cls(
            limits=limits,
            enforce_quotas=enforce_quotas,
        )

        update_quota_request.additional_properties = d
        return update_quota_request

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

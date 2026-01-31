from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PriceTier")


@_attrs_define
class PriceTier:
    """Volume pricing tier.

    Attributes:
        price_per_unit_cents (int): Price per unit in cents
        up_to (int | None | Unset): Maximum units for this tier (None = infinity)
        flat_fee_cents (int | None | Unset): Optional flat fee for this tier
    """

    price_per_unit_cents: int
    up_to: int | None | Unset = UNSET
    flat_fee_cents: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        price_per_unit_cents = self.price_per_unit_cents

        up_to: int | None | Unset
        if isinstance(self.up_to, Unset):
            up_to = UNSET
        else:
            up_to = self.up_to

        flat_fee_cents: int | None | Unset
        if isinstance(self.flat_fee_cents, Unset):
            flat_fee_cents = UNSET
        else:
            flat_fee_cents = self.flat_fee_cents

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "price_per_unit_cents": price_per_unit_cents,
            }
        )
        if up_to is not UNSET:
            field_dict["up_to"] = up_to
        if flat_fee_cents is not UNSET:
            field_dict["flat_fee_cents"] = flat_fee_cents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        price_per_unit_cents = d.pop("price_per_unit_cents")

        def _parse_up_to(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        up_to = _parse_up_to(d.pop("up_to", UNSET))

        def _parse_flat_fee_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        flat_fee_cents = _parse_flat_fee_cents(d.pop("flat_fee_cents", UNSET))

        price_tier = cls(
            price_per_unit_cents=price_per_unit_cents,
            up_to=up_to,
            flat_fee_cents=flat_fee_cents,
        )

        price_tier.additional_properties = d
        return price_tier

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

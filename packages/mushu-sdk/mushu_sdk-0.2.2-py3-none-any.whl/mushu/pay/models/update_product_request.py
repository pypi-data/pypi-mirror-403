from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProductRequest")


@_attrs_define
class UpdateProductRequest:
    """Request to update a product.

    Attributes:
        name (None | str | Unset): Updated name
        price_cents (int | None | Unset): Updated price
        active (bool | None | Unset): Whether product is active
        amount_micros (int | None | Unset): Updated amount in micro-dollars deposited to wallet
    """

    name: None | str | Unset = UNSET
    price_cents: int | None | Unset = UNSET
    active: bool | None | Unset = UNSET
    amount_micros: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        price_cents: int | None | Unset
        if isinstance(self.price_cents, Unset):
            price_cents = UNSET
        else:
            price_cents = self.price_cents

        active: bool | None | Unset
        if isinstance(self.active, Unset):
            active = UNSET
        else:
            active = self.active

        amount_micros: int | None | Unset
        if isinstance(self.amount_micros, Unset):
            amount_micros = UNSET
        else:
            amount_micros = self.amount_micros

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if price_cents is not UNSET:
            field_dict["price_cents"] = price_cents
        if active is not UNSET:
            field_dict["active"] = active
        if amount_micros is not UNSET:
            field_dict["amount_micros"] = amount_micros

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_price_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        price_cents = _parse_price_cents(d.pop("price_cents", UNSET))

        def _parse_active(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        active = _parse_active(d.pop("active", UNSET))

        def _parse_amount_micros(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        amount_micros = _parse_amount_micros(d.pop("amount_micros", UNSET))

        update_product_request = cls(
            name=name,
            price_cents=price_cents,
            active=active,
            amount_micros=amount_micros,
        )

        update_product_request.additional_properties = d
        return update_product_request

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

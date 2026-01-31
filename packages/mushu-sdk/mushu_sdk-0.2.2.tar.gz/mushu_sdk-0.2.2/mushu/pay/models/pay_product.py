from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.billing_model import BillingModel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.price_tier import PriceTier


T = TypeVar("T", bound="PayProduct")


@_attrs_define
class PayProduct:
    """Product response model.

    Attributes:
        org_id (str): Owning organization ID
        product_id (str): Unique product identifier
        name (str): Product name
        billing_model (BillingModel): Product billing model.
        price_cents (int): Base price in cents
        stripe_price_id (str): Stripe Price ID
        active (bool): Whether product is active
        created_at (str): ISO timestamp of creation
        amount_micros (int | None | Unset): Amount in micro-dollars deposited to wallet on purchase
        interval (None | str | Unset): Billing interval
        interval_amount_micros (int | None | Unset): Amount in micro-dollars deposited per billing period
        unit_name (None | str | Unset): Unit name
        price_per_unit_cents (int | None | Unset): Price per unit
        tiers (list[PriceTier] | None | Unset): Pricing tiers
    """

    org_id: str
    product_id: str
    name: str
    billing_model: BillingModel
    price_cents: int
    stripe_price_id: str
    active: bool
    created_at: str
    amount_micros: int | None | Unset = UNSET
    interval: None | str | Unset = UNSET
    interval_amount_micros: int | None | Unset = UNSET
    unit_name: None | str | Unset = UNSET
    price_per_unit_cents: int | None | Unset = UNSET
    tiers: list[PriceTier] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        product_id = self.product_id

        name = self.name

        billing_model = self.billing_model.value

        price_cents = self.price_cents

        stripe_price_id = self.stripe_price_id

        active = self.active

        created_at = self.created_at

        amount_micros: int | None | Unset
        if isinstance(self.amount_micros, Unset):
            amount_micros = UNSET
        else:
            amount_micros = self.amount_micros

        interval: None | str | Unset
        if isinstance(self.interval, Unset):
            interval = UNSET
        else:
            interval = self.interval

        interval_amount_micros: int | None | Unset
        if isinstance(self.interval_amount_micros, Unset):
            interval_amount_micros = UNSET
        else:
            interval_amount_micros = self.interval_amount_micros

        unit_name: None | str | Unset
        if isinstance(self.unit_name, Unset):
            unit_name = UNSET
        else:
            unit_name = self.unit_name

        price_per_unit_cents: int | None | Unset
        if isinstance(self.price_per_unit_cents, Unset):
            price_per_unit_cents = UNSET
        else:
            price_per_unit_cents = self.price_per_unit_cents

        tiers: list[dict[str, Any]] | None | Unset
        if isinstance(self.tiers, Unset):
            tiers = UNSET
        elif isinstance(self.tiers, list):
            tiers = []
            for tiers_type_0_item_data in self.tiers:
                tiers_type_0_item = tiers_type_0_item_data.to_dict()
                tiers.append(tiers_type_0_item)

        else:
            tiers = self.tiers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "product_id": product_id,
                "name": name,
                "billing_model": billing_model,
                "price_cents": price_cents,
                "stripe_price_id": stripe_price_id,
                "active": active,
                "created_at": created_at,
            }
        )
        if amount_micros is not UNSET:
            field_dict["amount_micros"] = amount_micros
        if interval is not UNSET:
            field_dict["interval"] = interval
        if interval_amount_micros is not UNSET:
            field_dict["interval_amount_micros"] = interval_amount_micros
        if unit_name is not UNSET:
            field_dict["unit_name"] = unit_name
        if price_per_unit_cents is not UNSET:
            field_dict["price_per_unit_cents"] = price_per_unit_cents
        if tiers is not UNSET:
            field_dict["tiers"] = tiers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.price_tier import PriceTier

        d = dict(src_dict)
        org_id = d.pop("org_id")

        product_id = d.pop("product_id")

        name = d.pop("name")

        billing_model = BillingModel(d.pop("billing_model"))

        price_cents = d.pop("price_cents")

        stripe_price_id = d.pop("stripe_price_id")

        active = d.pop("active")

        created_at = d.pop("created_at")

        def _parse_amount_micros(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        amount_micros = _parse_amount_micros(d.pop("amount_micros", UNSET))

        def _parse_interval(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        interval = _parse_interval(d.pop("interval", UNSET))

        def _parse_interval_amount_micros(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        interval_amount_micros = _parse_interval_amount_micros(
            d.pop("interval_amount_micros", UNSET)
        )

        def _parse_unit_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        unit_name = _parse_unit_name(d.pop("unit_name", UNSET))

        def _parse_price_per_unit_cents(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        price_per_unit_cents = _parse_price_per_unit_cents(d.pop("price_per_unit_cents", UNSET))

        def _parse_tiers(data: object) -> list[PriceTier] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tiers_type_0 = []
                _tiers_type_0 = data
                for tiers_type_0_item_data in _tiers_type_0:
                    tiers_type_0_item = PriceTier.from_dict(tiers_type_0_item_data)

                    tiers_type_0.append(tiers_type_0_item)

                return tiers_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PriceTier] | None | Unset, data)

        tiers = _parse_tiers(d.pop("tiers", UNSET))

        pay_product = cls(
            org_id=org_id,
            product_id=product_id,
            name=name,
            billing_model=billing_model,
            price_cents=price_cents,
            stripe_price_id=stripe_price_id,
            active=active,
            created_at=created_at,
            amount_micros=amount_micros,
            interval=interval,
            interval_amount_micros=interval_amount_micros,
            unit_name=unit_name,
            price_per_unit_cents=price_per_unit_cents,
            tiers=tiers,
        )

        pay_product.additional_properties = d
        return pay_product

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

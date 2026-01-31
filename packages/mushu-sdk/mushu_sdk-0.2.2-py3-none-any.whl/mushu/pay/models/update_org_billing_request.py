from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateOrgBillingRequest")


@_attrs_define
class UpdateOrgBillingRequest:
    """Request to update billing config.

    Attributes:
        name (None | str | Unset): Updated name
        stripe_secret_key (None | str | Unset): Updated Stripe secret key
        stripe_webhook_secret (None | str | Unset): Updated Stripe webhook secret
        free_tier_amount (int | None | Unset): Amount granted to new organizations in micro-dollars (0 to disable)
    """

    name: None | str | Unset = UNSET
    stripe_secret_key: None | str | Unset = UNSET
    stripe_webhook_secret: None | str | Unset = UNSET
    free_tier_amount: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        stripe_secret_key: None | str | Unset
        if isinstance(self.stripe_secret_key, Unset):
            stripe_secret_key = UNSET
        else:
            stripe_secret_key = self.stripe_secret_key

        stripe_webhook_secret: None | str | Unset
        if isinstance(self.stripe_webhook_secret, Unset):
            stripe_webhook_secret = UNSET
        else:
            stripe_webhook_secret = self.stripe_webhook_secret

        free_tier_amount: int | None | Unset
        if isinstance(self.free_tier_amount, Unset):
            free_tier_amount = UNSET
        else:
            free_tier_amount = self.free_tier_amount

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if stripe_secret_key is not UNSET:
            field_dict["stripe_secret_key"] = stripe_secret_key
        if stripe_webhook_secret is not UNSET:
            field_dict["stripe_webhook_secret"] = stripe_webhook_secret
        if free_tier_amount is not UNSET:
            field_dict["free_tier_amount"] = free_tier_amount

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

        def _parse_stripe_secret_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_secret_key = _parse_stripe_secret_key(d.pop("stripe_secret_key", UNSET))

        def _parse_stripe_webhook_secret(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_webhook_secret = _parse_stripe_webhook_secret(d.pop("stripe_webhook_secret", UNSET))

        def _parse_free_tier_amount(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        free_tier_amount = _parse_free_tier_amount(d.pop("free_tier_amount", UNSET))

        update_org_billing_request = cls(
            name=name,
            stripe_secret_key=stripe_secret_key,
            stripe_webhook_secret=stripe_webhook_secret,
            free_tier_amount=free_tier_amount,
        )

        update_org_billing_request.additional_properties = d
        return update_org_billing_request

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

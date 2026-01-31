from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WalletTransaction")


@_attrs_define
class WalletTransaction:
    """Wallet transaction response model.

    Attributes:
        org_id (str): Organization ID
        transaction_id (str): Transaction ID
        type_ (str): Transaction type (deposit, charge, refund)
        amount_micros (int): Amount in micro-dollars (positive=deposit, negative=charge)
        amount_usd (str): Amount formatted as USD
        balance_after (int): Balance after transaction in micro-dollars
        balance_after_usd (str): Balance after transaction formatted as USD
        description (str): Transaction description
        created_at (str): ISO timestamp
        stripe_payment_id (None | str | Unset): Stripe payment ID
        app_id (None | str | Unset): App that triggered this
    """

    org_id: str
    transaction_id: str
    type_: str
    amount_micros: int
    amount_usd: str
    balance_after: int
    balance_after_usd: str
    description: str
    created_at: str
    stripe_payment_id: None | str | Unset = UNSET
    app_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        transaction_id = self.transaction_id

        type_ = self.type_

        amount_micros = self.amount_micros

        amount_usd = self.amount_usd

        balance_after = self.balance_after

        balance_after_usd = self.balance_after_usd

        description = self.description

        created_at = self.created_at

        stripe_payment_id: None | str | Unset
        if isinstance(self.stripe_payment_id, Unset):
            stripe_payment_id = UNSET
        else:
            stripe_payment_id = self.stripe_payment_id

        app_id: None | str | Unset
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "transaction_id": transaction_id,
                "type": type_,
                "amount_micros": amount_micros,
                "amount_usd": amount_usd,
                "balance_after": balance_after,
                "balance_after_usd": balance_after_usd,
                "description": description,
                "created_at": created_at,
            }
        )
        if stripe_payment_id is not UNSET:
            field_dict["stripe_payment_id"] = stripe_payment_id
        if app_id is not UNSET:
            field_dict["app_id"] = app_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("org_id")

        transaction_id = d.pop("transaction_id")

        type_ = d.pop("type")

        amount_micros = d.pop("amount_micros")

        amount_usd = d.pop("amount_usd")

        balance_after = d.pop("balance_after")

        balance_after_usd = d.pop("balance_after_usd")

        description = d.pop("description")

        created_at = d.pop("created_at")

        def _parse_stripe_payment_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stripe_payment_id = _parse_stripe_payment_id(d.pop("stripe_payment_id", UNSET))

        def _parse_app_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        wallet_transaction = cls(
            org_id=org_id,
            transaction_id=transaction_id,
            type_=type_,
            amount_micros=amount_micros,
            amount_usd=amount_usd,
            balance_after=balance_after,
            balance_after_usd=balance_after_usd,
            description=description,
            created_at=created_at,
            stripe_payment_id=stripe_payment_id,
            app_id=app_id,
        )

        wallet_transaction.additional_properties = d
        return wallet_transaction

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

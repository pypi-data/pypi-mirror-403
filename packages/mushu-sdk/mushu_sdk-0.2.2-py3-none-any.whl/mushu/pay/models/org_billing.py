from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="OrgBilling")


@_attrs_define
class OrgBilling:
    """Organization billing response model.

    Attributes:
        org_id (str): Organization ID
        name (str): Billing config name
        has_stripe_key (bool): Whether Stripe key is configured
        has_webhook_secret (bool): Whether webhook secret is configured
        created_at (str): ISO timestamp of creation
        created_by (str): User ID who created this
        is_platform (bool | Unset): True if this is Mushu's own billing Default: False.
        free_tier_amount (int | Unset): Amount granted to new orgs in micro-dollars Default: 0.
        wallet_balance (int | Unset): Current wallet balance in micro-dollars Default: 0.
        wallet_balance_usd (str | Unset): Wallet balance formatted as USD Default: '$0.00'.
        auto_refill_enabled (bool | Unset): Whether auto-refill is enabled Default: False.
        auto_refill_product_id (None | str | Unset): Product for auto-refill
        auto_refill_threshold (int | Unset): Auto-refill threshold in micro-dollars Default: 0.
        has_payment_method (bool | Unset): Whether a payment method is saved Default: False.
    """

    org_id: str
    name: str
    has_stripe_key: bool
    has_webhook_secret: bool
    created_at: str
    created_by: str
    is_platform: bool | Unset = False
    free_tier_amount: int | Unset = 0
    wallet_balance: int | Unset = 0
    wallet_balance_usd: str | Unset = "$0.00"
    auto_refill_enabled: bool | Unset = False
    auto_refill_product_id: None | str | Unset = UNSET
    auto_refill_threshold: int | Unset = 0
    has_payment_method: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        name = self.name

        has_stripe_key = self.has_stripe_key

        has_webhook_secret = self.has_webhook_secret

        created_at = self.created_at

        created_by = self.created_by

        is_platform = self.is_platform

        free_tier_amount = self.free_tier_amount

        wallet_balance = self.wallet_balance

        wallet_balance_usd = self.wallet_balance_usd

        auto_refill_enabled = self.auto_refill_enabled

        auto_refill_product_id: None | str | Unset
        if isinstance(self.auto_refill_product_id, Unset):
            auto_refill_product_id = UNSET
        else:
            auto_refill_product_id = self.auto_refill_product_id

        auto_refill_threshold = self.auto_refill_threshold

        has_payment_method = self.has_payment_method

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "name": name,
                "has_stripe_key": has_stripe_key,
                "has_webhook_secret": has_webhook_secret,
                "created_at": created_at,
                "created_by": created_by,
            }
        )
        if is_platform is not UNSET:
            field_dict["is_platform"] = is_platform
        if free_tier_amount is not UNSET:
            field_dict["free_tier_amount"] = free_tier_amount
        if wallet_balance is not UNSET:
            field_dict["wallet_balance"] = wallet_balance
        if wallet_balance_usd is not UNSET:
            field_dict["wallet_balance_usd"] = wallet_balance_usd
        if auto_refill_enabled is not UNSET:
            field_dict["auto_refill_enabled"] = auto_refill_enabled
        if auto_refill_product_id is not UNSET:
            field_dict["auto_refill_product_id"] = auto_refill_product_id
        if auto_refill_threshold is not UNSET:
            field_dict["auto_refill_threshold"] = auto_refill_threshold
        if has_payment_method is not UNSET:
            field_dict["has_payment_method"] = has_payment_method

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("org_id")

        name = d.pop("name")

        has_stripe_key = d.pop("has_stripe_key")

        has_webhook_secret = d.pop("has_webhook_secret")

        created_at = d.pop("created_at")

        created_by = d.pop("created_by")

        is_platform = d.pop("is_platform", UNSET)

        free_tier_amount = d.pop("free_tier_amount", UNSET)

        wallet_balance = d.pop("wallet_balance", UNSET)

        wallet_balance_usd = d.pop("wallet_balance_usd", UNSET)

        auto_refill_enabled = d.pop("auto_refill_enabled", UNSET)

        def _parse_auto_refill_product_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        auto_refill_product_id = _parse_auto_refill_product_id(
            d.pop("auto_refill_product_id", UNSET)
        )

        auto_refill_threshold = d.pop("auto_refill_threshold", UNSET)

        has_payment_method = d.pop("has_payment_method", UNSET)

        org_billing = cls(
            org_id=org_id,
            name=name,
            has_stripe_key=has_stripe_key,
            has_webhook_secret=has_webhook_secret,
            created_at=created_at,
            created_by=created_by,
            is_platform=is_platform,
            free_tier_amount=free_tier_amount,
            wallet_balance=wallet_balance,
            wallet_balance_usd=wallet_balance_usd,
            auto_refill_enabled=auto_refill_enabled,
            auto_refill_product_id=auto_refill_product_id,
            auto_refill_threshold=auto_refill_threshold,
            has_payment_method=has_payment_method,
        )

        org_billing.additional_properties = d
        return org_billing

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

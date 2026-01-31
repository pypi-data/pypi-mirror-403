from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.wallet_operation_type import WalletOperationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="WalletOperationRequest")


@_attrs_define
class WalletOperationRequest:
    """Request to deposit or charge the wallet.

    Attributes:
        operation (WalletOperationType): Wallet operation type.
        amount_micros (int): Amount in micro-dollars
        description (str): Reason for the operation
        app_id (None | str | Unset): App that triggered this (for charges)
    """

    operation: WalletOperationType
    amount_micros: int
    description: str
    app_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        operation = self.operation.value

        amount_micros = self.amount_micros

        description = self.description

        app_id: None | str | Unset
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "operation": operation,
                "amount_micros": amount_micros,
                "description": description,
            }
        )
        if app_id is not UNSET:
            field_dict["app_id"] = app_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        operation = WalletOperationType(d.pop("operation"))

        amount_micros = d.pop("amount_micros")

        description = d.pop("description")

        def _parse_app_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        wallet_operation_request = cls(
            operation=operation,
            amount_micros=amount_micros,
            description=description,
            app_id=app_id,
        )

        wallet_operation_request.additional_properties = d
        return wallet_operation_request

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

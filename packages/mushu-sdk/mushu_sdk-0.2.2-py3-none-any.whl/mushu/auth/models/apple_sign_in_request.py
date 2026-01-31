from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AppleSignInRequest")


@_attrs_define
class AppleSignInRequest:
    """Request to sign in with Apple.

    Attributes:
        id_token (str): Apple ID token from Sign In with Apple
        access_code (str): Apple authorization code
        nonce (str): Nonce used during sign in (for validation)
        given_name (None | str | Unset): User's given name
        family_name (None | str | Unset): User's family name
    """

    id_token: str
    access_code: str
    nonce: str
    given_name: None | str | Unset = UNSET
    family_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id_token = self.id_token

        access_code = self.access_code

        nonce = self.nonce

        given_name: None | str | Unset
        if isinstance(self.given_name, Unset):
            given_name = UNSET
        else:
            given_name = self.given_name

        family_name: None | str | Unset
        if isinstance(self.family_name, Unset):
            family_name = UNSET
        else:
            family_name = self.family_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id_token": id_token,
                "access_code": access_code,
                "nonce": nonce,
            }
        )
        if given_name is not UNSET:
            field_dict["given_name"] = given_name
        if family_name is not UNSET:
            field_dict["family_name"] = family_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id_token = d.pop("id_token")

        access_code = d.pop("access_code")

        nonce = d.pop("nonce")

        def _parse_given_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        given_name = _parse_given_name(d.pop("given_name", UNSET))

        def _parse_family_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        family_name = _parse_family_name(d.pop("family_name", UNSET))

        apple_sign_in_request = cls(
            id_token=id_token,
            access_code=access_code,
            nonce=nonce,
            given_name=given_name,
            family_name=family_name,
        )

        apple_sign_in_request.additional_properties = d
        return apple_sign_in_request

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

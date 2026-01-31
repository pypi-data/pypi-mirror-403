from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GoogleSignInRequest")


@_attrs_define
class GoogleSignInRequest:
    """Request to sign in with Google.

    Attributes:
        client_id (str): Google client ID used by the app
        nonce (str): Nonce used during sign in (for validation)
        authorization_code (None | str | Unset): Google authorization code from SDK
        id_token (None | str | Unset): Google ID token from One Tap web flow
        redirect_uri (None | str | Unset): Redirect URI used for code exchange
    """

    client_id: str
    nonce: str
    authorization_code: None | str | Unset = UNSET
    id_token: None | str | Unset = UNSET
    redirect_uri: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client_id = self.client_id

        nonce = self.nonce

        authorization_code: None | str | Unset
        if isinstance(self.authorization_code, Unset):
            authorization_code = UNSET
        else:
            authorization_code = self.authorization_code

        id_token: None | str | Unset
        if isinstance(self.id_token, Unset):
            id_token = UNSET
        else:
            id_token = self.id_token

        redirect_uri: None | str | Unset
        if isinstance(self.redirect_uri, Unset):
            redirect_uri = UNSET
        else:
            redirect_uri = self.redirect_uri

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "client_id": client_id,
                "nonce": nonce,
            }
        )
        if authorization_code is not UNSET:
            field_dict["authorization_code"] = authorization_code
        if id_token is not UNSET:
            field_dict["id_token"] = id_token
        if redirect_uri is not UNSET:
            field_dict["redirect_uri"] = redirect_uri

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        client_id = d.pop("client_id")

        nonce = d.pop("nonce")

        def _parse_authorization_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        authorization_code = _parse_authorization_code(d.pop("authorization_code", UNSET))

        def _parse_id_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id_token = _parse_id_token(d.pop("id_token", UNSET))

        def _parse_redirect_uri(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        redirect_uri = _parse_redirect_uri(d.pop("redirect_uri", UNSET))

        google_sign_in_request = cls(
            client_id=client_id,
            nonce=nonce,
            authorization_code=authorization_code,
            id_token=id_token,
            redirect_uri=redirect_uri,
        )

        google_sign_in_request.additional_properties = d
        return google_sign_in_request

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

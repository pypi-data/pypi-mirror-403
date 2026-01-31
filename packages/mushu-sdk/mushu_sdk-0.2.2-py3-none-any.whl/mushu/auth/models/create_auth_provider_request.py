from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.auth_provider_type import AuthProviderType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateAuthProviderRequest")


@_attrs_define
class CreateAuthProviderRequest:
    """Request to create an auth provider configuration.

    Attributes:
        provider_type (AuthProviderType): Supported authentication provider types.
        enabled (bool | Unset): Whether the provider is enabled Default: True.
        apple_team_id (None | str | Unset): Apple Team ID
        apple_key_id (None | str | Unset): Apple Key ID
        apple_bundle_ids (list[str] | None | Unset): iOS app bundle IDs
        apple_services_id (None | str | Unset): Apple Services ID for web OAuth
        apple_private_key (None | str | Unset): Apple private key (P8 format)
        google_client_id (None | str | Unset): Google OAuth client ID
        google_client_secret (None | str | Unset): Google OAuth client secret
    """

    provider_type: AuthProviderType
    enabled: bool | Unset = True
    apple_team_id: None | str | Unset = UNSET
    apple_key_id: None | str | Unset = UNSET
    apple_bundle_ids: list[str] | None | Unset = UNSET
    apple_services_id: None | str | Unset = UNSET
    apple_private_key: None | str | Unset = UNSET
    google_client_id: None | str | Unset = UNSET
    google_client_secret: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider_type = self.provider_type.value

        enabled = self.enabled

        apple_team_id: None | str | Unset
        if isinstance(self.apple_team_id, Unset):
            apple_team_id = UNSET
        else:
            apple_team_id = self.apple_team_id

        apple_key_id: None | str | Unset
        if isinstance(self.apple_key_id, Unset):
            apple_key_id = UNSET
        else:
            apple_key_id = self.apple_key_id

        apple_bundle_ids: list[str] | None | Unset
        if isinstance(self.apple_bundle_ids, Unset):
            apple_bundle_ids = UNSET
        elif isinstance(self.apple_bundle_ids, list):
            apple_bundle_ids = self.apple_bundle_ids

        else:
            apple_bundle_ids = self.apple_bundle_ids

        apple_services_id: None | str | Unset
        if isinstance(self.apple_services_id, Unset):
            apple_services_id = UNSET
        else:
            apple_services_id = self.apple_services_id

        apple_private_key: None | str | Unset
        if isinstance(self.apple_private_key, Unset):
            apple_private_key = UNSET
        else:
            apple_private_key = self.apple_private_key

        google_client_id: None | str | Unset
        if isinstance(self.google_client_id, Unset):
            google_client_id = UNSET
        else:
            google_client_id = self.google_client_id

        google_client_secret: None | str | Unset
        if isinstance(self.google_client_secret, Unset):
            google_client_secret = UNSET
        else:
            google_client_secret = self.google_client_secret

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider_type": provider_type,
            }
        )
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if apple_team_id is not UNSET:
            field_dict["apple_team_id"] = apple_team_id
        if apple_key_id is not UNSET:
            field_dict["apple_key_id"] = apple_key_id
        if apple_bundle_ids is not UNSET:
            field_dict["apple_bundle_ids"] = apple_bundle_ids
        if apple_services_id is not UNSET:
            field_dict["apple_services_id"] = apple_services_id
        if apple_private_key is not UNSET:
            field_dict["apple_private_key"] = apple_private_key
        if google_client_id is not UNSET:
            field_dict["google_client_id"] = google_client_id
        if google_client_secret is not UNSET:
            field_dict["google_client_secret"] = google_client_secret

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provider_type = AuthProviderType(d.pop("provider_type"))

        enabled = d.pop("enabled", UNSET)

        def _parse_apple_team_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        apple_team_id = _parse_apple_team_id(d.pop("apple_team_id", UNSET))

        def _parse_apple_key_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        apple_key_id = _parse_apple_key_id(d.pop("apple_key_id", UNSET))

        def _parse_apple_bundle_ids(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                apple_bundle_ids_type_0 = cast(list[str], data)

                return apple_bundle_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        apple_bundle_ids = _parse_apple_bundle_ids(d.pop("apple_bundle_ids", UNSET))

        def _parse_apple_services_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        apple_services_id = _parse_apple_services_id(d.pop("apple_services_id", UNSET))

        def _parse_apple_private_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        apple_private_key = _parse_apple_private_key(d.pop("apple_private_key", UNSET))

        def _parse_google_client_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        google_client_id = _parse_google_client_id(d.pop("google_client_id", UNSET))

        def _parse_google_client_secret(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        google_client_secret = _parse_google_client_secret(d.pop("google_client_secret", UNSET))

        create_auth_provider_request = cls(
            provider_type=provider_type,
            enabled=enabled,
            apple_team_id=apple_team_id,
            apple_key_id=apple_key_id,
            apple_bundle_ids=apple_bundle_ids,
            apple_services_id=apple_services_id,
            apple_private_key=apple_private_key,
            google_client_id=google_client_id,
            google_client_secret=google_client_secret,
        )

        create_auth_provider_request.additional_properties = d
        return create_auth_provider_request

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

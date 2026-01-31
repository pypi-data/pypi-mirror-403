from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.auth_provider_type import AuthProviderType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AuthProvider")


@_attrs_define
class AuthProvider:
    """Auth provider configuration response.

    Attributes:
        app_id (str): App ID
        provider_type (AuthProviderType): Supported authentication provider types.
        enabled (bool): Whether the provider is enabled
        created_at (str): ISO timestamp of creation
        updated_at (str): ISO timestamp of last update
        is_configured (bool): Whether provider has minimum required config
        apple_team_id (None | str | Unset): Apple Team ID
        apple_key_id (None | str | Unset): Apple Key ID
        apple_bundle_ids (list[str] | None | Unset): iOS app bundle IDs
        apple_services_id (None | str | Unset): Apple Services ID for web OAuth
        google_client_id (None | str | Unset): Google OAuth client ID
    """

    app_id: str
    provider_type: AuthProviderType
    enabled: bool
    created_at: str
    updated_at: str
    is_configured: bool
    apple_team_id: None | str | Unset = UNSET
    apple_key_id: None | str | Unset = UNSET
    apple_bundle_ids: list[str] | None | Unset = UNSET
    apple_services_id: None | str | Unset = UNSET
    google_client_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        provider_type = self.provider_type.value

        enabled = self.enabled

        created_at = self.created_at

        updated_at = self.updated_at

        is_configured = self.is_configured

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

        google_client_id: None | str | Unset
        if isinstance(self.google_client_id, Unset):
            google_client_id = UNSET
        else:
            google_client_id = self.google_client_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "provider_type": provider_type,
                "enabled": enabled,
                "created_at": created_at,
                "updated_at": updated_at,
                "is_configured": is_configured,
            }
        )
        if apple_team_id is not UNSET:
            field_dict["apple_team_id"] = apple_team_id
        if apple_key_id is not UNSET:
            field_dict["apple_key_id"] = apple_key_id
        if apple_bundle_ids is not UNSET:
            field_dict["apple_bundle_ids"] = apple_bundle_ids
        if apple_services_id is not UNSET:
            field_dict["apple_services_id"] = apple_services_id
        if google_client_id is not UNSET:
            field_dict["google_client_id"] = google_client_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_id = d.pop("app_id")

        provider_type = AuthProviderType(d.pop("provider_type"))

        enabled = d.pop("enabled")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        is_configured = d.pop("is_configured")

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

        def _parse_google_client_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        google_client_id = _parse_google_client_id(d.pop("google_client_id", UNSET))

        auth_provider = cls(
            app_id=app_id,
            provider_type=provider_type,
            enabled=enabled,
            created_at=created_at,
            updated_at=updated_at,
            is_configured=is_configured,
            apple_team_id=apple_team_id,
            apple_key_id=apple_key_id,
            apple_bundle_ids=apple_bundle_ids,
            apple_services_id=apple_services_id,
            google_client_id=google_client_id,
        )

        auth_provider.additional_properties = d
        return auth_provider

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

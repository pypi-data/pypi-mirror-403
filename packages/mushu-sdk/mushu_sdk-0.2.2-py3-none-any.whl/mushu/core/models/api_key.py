from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_key_scope import ApiKeyScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKey")


@_attrs_define
class ApiKey:
    """API key for server-to-server authentication.

    Attributes:
        key_id (str): Unique key ID
        app_id (str): App this key belongs to
        name (str): Human-readable key name
        prefix (str): Key prefix for identification (first 8 chars)
        scope (ApiKeyScope): API key scope/permission level.
        created_at (str): When the key was created
        created_by (str): User who created the key
        last_used_at (None | str | Unset): When the key was last used
        expires_at (None | str | Unset): When the key expires (optional)
        revoked_at (None | str | Unset): When the key was revoked
    """

    key_id: str
    app_id: str
    name: str
    prefix: str
    scope: ApiKeyScope
    created_at: str
    created_by: str
    last_used_at: None | str | Unset = UNSET
    expires_at: None | str | Unset = UNSET
    revoked_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key_id = self.key_id

        app_id = self.app_id

        name = self.name

        prefix = self.prefix

        scope = self.scope.value

        created_at = self.created_at

        created_by = self.created_by

        last_used_at: None | str | Unset
        if isinstance(self.last_used_at, Unset):
            last_used_at = UNSET
        else:
            last_used_at = self.last_used_at

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = self.expires_at

        revoked_at: None | str | Unset
        if isinstance(self.revoked_at, Unset):
            revoked_at = UNSET
        else:
            revoked_at = self.revoked_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key_id": key_id,
                "app_id": app_id,
                "name": name,
                "prefix": prefix,
                "scope": scope,
                "created_at": created_at,
                "created_by": created_by,
            }
        )
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if revoked_at is not UNSET:
            field_dict["revoked_at"] = revoked_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key_id = d.pop("key_id")

        app_id = d.pop("app_id")

        name = d.pop("name")

        prefix = d.pop("prefix")

        scope = ApiKeyScope(d.pop("scope"))

        created_at = d.pop("created_at")

        created_by = d.pop("created_by")

        def _parse_last_used_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at", UNSET))

        def _parse_expires_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        def _parse_revoked_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        revoked_at = _parse_revoked_at(d.pop("revoked_at", UNSET))

        api_key = cls(
            key_id=key_id,
            app_id=app_id,
            name=name,
            prefix=prefix,
            scope=scope,
            created_at=created_at,
            created_by=created_by,
            last_used_at=last_used_at,
            expires_at=expires_at,
            revoked_at=revoked_at,
        )

        api_key.additional_properties = d
        return api_key

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

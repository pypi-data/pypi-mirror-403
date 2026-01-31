from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_key_scope import ApiKeyScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateApiKeyResponse")


@_attrs_define
class CreateApiKeyResponse:
    """Response after creating an API key (only time full key is returned).

    Attributes:
        key_id (str): Unique key ID
        app_id (str): App this key belongs to
        name (str): Key name
        key (str): The full API key (only shown once)
        prefix (str): Key prefix
        scope (ApiKeyScope): API key scope/permission level.
        created_at (str): When the key was created
        expires_at (None | str | Unset): When the key expires
    """

    key_id: str
    app_id: str
    name: str
    key: str
    prefix: str
    scope: ApiKeyScope
    created_at: str
    expires_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key_id = self.key_id

        app_id = self.app_id

        name = self.name

        key = self.key

        prefix = self.prefix

        scope = self.scope.value

        created_at = self.created_at

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = self.expires_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key_id": key_id,
                "app_id": app_id,
                "name": name,
                "key": key,
                "prefix": prefix,
                "scope": scope,
                "created_at": created_at,
            }
        )
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key_id = d.pop("key_id")

        app_id = d.pop("app_id")

        name = d.pop("name")

        key = d.pop("key")

        prefix = d.pop("prefix")

        scope = ApiKeyScope(d.pop("scope"))

        created_at = d.pop("created_at")

        def _parse_expires_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        create_api_key_response = cls(
            key_id=key_id,
            app_id=app_id,
            name=name,
            key=key,
            prefix=prefix,
            scope=scope,
            created_at=created_at,
            expires_at=expires_at,
        )

        create_api_key_response.additional_properties = d
        return create_api_key_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_key_scope import ApiKeyScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidateApiKeyResponse")


@_attrs_define
class ValidateApiKeyResponse:
    """Response from validating an API key.

    Attributes:
        valid (bool): Whether the key is valid
        key_id (None | str | Unset): Key ID if valid
        app_id (None | str | Unset): App ID if valid
        org_id (None | str | Unset): Org ID if valid
        scope (ApiKeyScope | None | Unset): Key scope if valid
        error (None | str | Unset): Error message if invalid
    """

    valid: bool
    key_id: None | str | Unset = UNSET
    app_id: None | str | Unset = UNSET
    org_id: None | str | Unset = UNSET
    scope: ApiKeyScope | None | Unset = UNSET
    error: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        valid = self.valid

        key_id: None | str | Unset
        if isinstance(self.key_id, Unset):
            key_id = UNSET
        else:
            key_id = self.key_id

        app_id: None | str | Unset
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        org_id: None | str | Unset
        if isinstance(self.org_id, Unset):
            org_id = UNSET
        else:
            org_id = self.org_id

        scope: None | str | Unset
        if isinstance(self.scope, Unset):
            scope = UNSET
        elif isinstance(self.scope, ApiKeyScope):
            scope = self.scope.value
        else:
            scope = self.scope

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "valid": valid,
            }
        )
        if key_id is not UNSET:
            field_dict["key_id"] = key_id
        if app_id is not UNSET:
            field_dict["app_id"] = app_id
        if org_id is not UNSET:
            field_dict["org_id"] = org_id
        if scope is not UNSET:
            field_dict["scope"] = scope
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        valid = d.pop("valid")

        def _parse_key_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        key_id = _parse_key_id(d.pop("key_id", UNSET))

        def _parse_app_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        def _parse_org_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        org_id = _parse_org_id(d.pop("org_id", UNSET))

        def _parse_scope(data: object) -> ApiKeyScope | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                scope_type_0 = ApiKeyScope(data)

                return scope_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ApiKeyScope | None | Unset, data)

        scope = _parse_scope(d.pop("scope", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        validate_api_key_response = cls(
            valid=valid,
            key_id=key_id,
            app_id=app_id,
            org_id=org_id,
            scope=scope,
            error=error,
        )

        validate_api_key_response.additional_properties = d
        return validate_api_key_response

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

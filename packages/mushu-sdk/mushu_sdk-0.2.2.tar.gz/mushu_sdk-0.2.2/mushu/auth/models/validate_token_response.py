from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_type import UserType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidateTokenResponse")


@_attrs_define
class ValidateTokenResponse:
    """Response from token validation (used by other services).

    Attributes:
        valid (bool): Whether the token is valid
        user_id (None | str | Unset): User ID if token is valid
        user_type (None | Unset | UserType): User type if token is valid
        email (None | str | Unset): User email if available
        app_id (None | str | Unset): App ID if token is valid
    """

    valid: bool
    user_id: None | str | Unset = UNSET
    user_type: None | Unset | UserType = UNSET
    email: None | str | Unset = UNSET
    app_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        valid = self.valid

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        user_type: None | str | Unset
        if isinstance(self.user_type, Unset):
            user_type = UNSET
        elif isinstance(self.user_type, UserType):
            user_type = self.user_type.value
        else:
            user_type = self.user_type

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        app_id: None | str | Unset
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "valid": valid,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if user_type is not UNSET:
            field_dict["user_type"] = user_type
        if email is not UNSET:
            field_dict["email"] = email
        if app_id is not UNSET:
            field_dict["app_id"] = app_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        valid = d.pop("valid")

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_user_type(data: object) -> None | Unset | UserType:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                user_type_type_0 = UserType(data)

                return user_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UserType, data)

        user_type = _parse_user_type(d.pop("user_type", UNSET))

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_app_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        validate_token_response = cls(
            valid=valid,
            user_id=user_id,
            user_type=user_type,
            email=email,
            app_id=app_id,
        )

        validate_token_response.additional_properties = d
        return validate_token_response

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

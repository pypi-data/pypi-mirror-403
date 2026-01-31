from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.session_tokens import SessionTokens
    from ..models.user import User


T = TypeVar("T", bound="SessionResponse")


@_attrs_define
class SessionResponse:
    """Response containing user and session tokens.

    Attributes:
        user (User): User profile.
        tokens (SessionTokens): Access and refresh tokens.
    """

    user: User
    tokens: SessionTokens
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user = self.user.to_dict()

        tokens = self.tokens.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user": user,
                "tokens": tokens,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_tokens import SessionTokens
        from ..models.user import User

        d = dict(src_dict)
        user = User.from_dict(d.pop("user"))

        tokens = SessionTokens.from_dict(d.pop("tokens"))

        session_response = cls(
            user=user,
            tokens=tokens,
        )

        session_response.additional_properties = d
        return session_response

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

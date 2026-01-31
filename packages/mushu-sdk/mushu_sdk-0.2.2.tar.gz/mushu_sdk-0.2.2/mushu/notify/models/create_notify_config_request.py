from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateNotifyConfigRequest")


@_attrs_define
class CreateNotifyConfigRequest:
    """Request to create notification config for an app.

    Attributes:
        org_id (str): Organization ID that owns this app
        bundle_id (None | str | Unset): iOS app bundle ID
        team_id (None | str | Unset): Apple Developer Team ID
        key_id (None | str | Unset): APNs Key ID
        private_key (None | str | Unset): APNs private key (.p8 contents)
        use_sandbox (bool | Unset): Use APNs sandbox environment Default: True.
    """

    org_id: str
    bundle_id: None | str | Unset = UNSET
    team_id: None | str | Unset = UNSET
    key_id: None | str | Unset = UNSET
    private_key: None | str | Unset = UNSET
    use_sandbox: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        bundle_id: None | str | Unset
        if isinstance(self.bundle_id, Unset):
            bundle_id = UNSET
        else:
            bundle_id = self.bundle_id

        team_id: None | str | Unset
        if isinstance(self.team_id, Unset):
            team_id = UNSET
        else:
            team_id = self.team_id

        key_id: None | str | Unset
        if isinstance(self.key_id, Unset):
            key_id = UNSET
        else:
            key_id = self.key_id

        private_key: None | str | Unset
        if isinstance(self.private_key, Unset):
            private_key = UNSET
        else:
            private_key = self.private_key

        use_sandbox = self.use_sandbox

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
            }
        )
        if bundle_id is not UNSET:
            field_dict["bundle_id"] = bundle_id
        if team_id is not UNSET:
            field_dict["team_id"] = team_id
        if key_id is not UNSET:
            field_dict["key_id"] = key_id
        if private_key is not UNSET:
            field_dict["private_key"] = private_key
        if use_sandbox is not UNSET:
            field_dict["use_sandbox"] = use_sandbox

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("org_id")

        def _parse_bundle_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bundle_id = _parse_bundle_id(d.pop("bundle_id", UNSET))

        def _parse_team_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        team_id = _parse_team_id(d.pop("team_id", UNSET))

        def _parse_key_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        key_id = _parse_key_id(d.pop("key_id", UNSET))

        def _parse_private_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        private_key = _parse_private_key(d.pop("private_key", UNSET))

        use_sandbox = d.pop("use_sandbox", UNSET)

        create_notify_config_request = cls(
            org_id=org_id,
            bundle_id=bundle_id,
            team_id=team_id,
            key_id=key_id,
            private_key=private_key,
            use_sandbox=use_sandbox,
        )

        create_notify_config_request.additional_properties = d
        return create_notify_config_request

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

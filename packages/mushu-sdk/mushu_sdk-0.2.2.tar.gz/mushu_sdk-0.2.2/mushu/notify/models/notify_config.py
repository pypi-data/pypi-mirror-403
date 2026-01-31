from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NotifyConfig")


@_attrs_define
class NotifyConfig:
    """Notification configuration for an app.

    Attributes:
        app_id (str): App identifier
        org_id (str): Organization ID that owns this app
        created_at (str): Creation timestamp
        created_by (str): User ID who created this config
        bundle_id (None | str | Unset): iOS app bundle ID
        team_id (None | str | Unset): Apple Developer Team ID
        key_id (None | str | Unset): APNs Key ID
        use_sandbox (bool | Unset): Using APNs sandbox Default: True.
        email_domain (None | str | Unset): Verified email domain
        email_domain_status (None | str | Unset): Domain verification status
        email_from_name (None | str | Unset): Default sender name
        email_verified_at (None | str | Unset): When email domain was verified
        push_enabled (bool | Unset): Whether push notifications are configured Default: False.
        email_enabled (bool | Unset): Whether email is configured and verified Default: False.
    """

    app_id: str
    org_id: str
    created_at: str
    created_by: str
    bundle_id: None | str | Unset = UNSET
    team_id: None | str | Unset = UNSET
    key_id: None | str | Unset = UNSET
    use_sandbox: bool | Unset = True
    email_domain: None | str | Unset = UNSET
    email_domain_status: None | str | Unset = UNSET
    email_from_name: None | str | Unset = UNSET
    email_verified_at: None | str | Unset = UNSET
    push_enabled: bool | Unset = False
    email_enabled: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        org_id = self.org_id

        created_at = self.created_at

        created_by = self.created_by

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

        use_sandbox = self.use_sandbox

        email_domain: None | str | Unset
        if isinstance(self.email_domain, Unset):
            email_domain = UNSET
        else:
            email_domain = self.email_domain

        email_domain_status: None | str | Unset
        if isinstance(self.email_domain_status, Unset):
            email_domain_status = UNSET
        else:
            email_domain_status = self.email_domain_status

        email_from_name: None | str | Unset
        if isinstance(self.email_from_name, Unset):
            email_from_name = UNSET
        else:
            email_from_name = self.email_from_name

        email_verified_at: None | str | Unset
        if isinstance(self.email_verified_at, Unset):
            email_verified_at = UNSET
        else:
            email_verified_at = self.email_verified_at

        push_enabled = self.push_enabled

        email_enabled = self.email_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "org_id": org_id,
                "created_at": created_at,
                "created_by": created_by,
            }
        )
        if bundle_id is not UNSET:
            field_dict["bundle_id"] = bundle_id
        if team_id is not UNSET:
            field_dict["team_id"] = team_id
        if key_id is not UNSET:
            field_dict["key_id"] = key_id
        if use_sandbox is not UNSET:
            field_dict["use_sandbox"] = use_sandbox
        if email_domain is not UNSET:
            field_dict["email_domain"] = email_domain
        if email_domain_status is not UNSET:
            field_dict["email_domain_status"] = email_domain_status
        if email_from_name is not UNSET:
            field_dict["email_from_name"] = email_from_name
        if email_verified_at is not UNSET:
            field_dict["email_verified_at"] = email_verified_at
        if push_enabled is not UNSET:
            field_dict["push_enabled"] = push_enabled
        if email_enabled is not UNSET:
            field_dict["email_enabled"] = email_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        app_id = d.pop("app_id")

        org_id = d.pop("org_id")

        created_at = d.pop("created_at")

        created_by = d.pop("created_by")

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

        use_sandbox = d.pop("use_sandbox", UNSET)

        def _parse_email_domain(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_domain = _parse_email_domain(d.pop("email_domain", UNSET))

        def _parse_email_domain_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_domain_status = _parse_email_domain_status(d.pop("email_domain_status", UNSET))

        def _parse_email_from_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_from_name = _parse_email_from_name(d.pop("email_from_name", UNSET))

        def _parse_email_verified_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_verified_at = _parse_email_verified_at(d.pop("email_verified_at", UNSET))

        push_enabled = d.pop("push_enabled", UNSET)

        email_enabled = d.pop("email_enabled", UNSET)

        notify_config = cls(
            app_id=app_id,
            org_id=org_id,
            created_at=created_at,
            created_by=created_by,
            bundle_id=bundle_id,
            team_id=team_id,
            key_id=key_id,
            use_sandbox=use_sandbox,
            email_domain=email_domain,
            email_domain_status=email_domain_status,
            email_from_name=email_from_name,
            email_verified_at=email_verified_at,
            push_enabled=push_enabled,
            email_enabled=email_enabled,
        )

        notify_config.additional_properties = d
        return notify_config

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

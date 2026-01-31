from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_payload import AlertPayload
    from ..models.send_push_request_data_type_0 import SendPushRequestDataType0


T = TypeVar("T", bound="SendPushRequest")


@_attrs_define
class SendPushRequest:
    """Request to send push notification.

    Attributes:
        user_id (str): Target user ID
        alert (AlertPayload | None | Unset): Alert payload
        badge (int | None | Unset): Badge count
        sound (None | str | Unset): Sound name
        content_available (bool | Unset): Silent/background push Default: False.
        data (None | SendPushRequestDataType0 | Unset): Custom data payload
    """

    user_id: str
    alert: AlertPayload | None | Unset = UNSET
    badge: int | None | Unset = UNSET
    sound: None | str | Unset = UNSET
    content_available: bool | Unset = False
    data: None | SendPushRequestDataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alert_payload import AlertPayload
        from ..models.send_push_request_data_type_0 import SendPushRequestDataType0

        user_id = self.user_id

        alert: dict[str, Any] | None | Unset
        if isinstance(self.alert, Unset):
            alert = UNSET
        elif isinstance(self.alert, AlertPayload):
            alert = self.alert.to_dict()
        else:
            alert = self.alert

        badge: int | None | Unset
        if isinstance(self.badge, Unset):
            badge = UNSET
        else:
            badge = self.badge

        sound: None | str | Unset
        if isinstance(self.sound, Unset):
            sound = UNSET
        else:
            sound = self.sound

        content_available = self.content_available

        data: dict[str, Any] | None | Unset
        if isinstance(self.data, Unset):
            data = UNSET
        elif isinstance(self.data, SendPushRequestDataType0):
            data = self.data.to_dict()
        else:
            data = self.data

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
            }
        )
        if alert is not UNSET:
            field_dict["alert"] = alert
        if badge is not UNSET:
            field_dict["badge"] = badge
        if sound is not UNSET:
            field_dict["sound"] = sound
        if content_available is not UNSET:
            field_dict["content_available"] = content_available
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_payload import AlertPayload
        from ..models.send_push_request_data_type_0 import SendPushRequestDataType0

        d = dict(src_dict)
        user_id = d.pop("user_id")

        def _parse_alert(data: object) -> AlertPayload | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                alert_type_0 = AlertPayload.from_dict(data)

                return alert_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AlertPayload | None | Unset, data)

        alert = _parse_alert(d.pop("alert", UNSET))

        def _parse_badge(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        badge = _parse_badge(d.pop("badge", UNSET))

        def _parse_sound(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sound = _parse_sound(d.pop("sound", UNSET))

        content_available = d.pop("content_available", UNSET)

        def _parse_data(data: object) -> None | SendPushRequestDataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = SendPushRequestDataType0.from_dict(data)

                return data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SendPushRequestDataType0 | Unset, data)

        data = _parse_data(d.pop("data", UNSET))

        send_push_request = cls(
            user_id=user_id,
            alert=alert,
            badge=badge,
            sound=sound,
            content_available=content_available,
            data=data,
        )

        send_push_request.additional_properties = d
        return send_push_request

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

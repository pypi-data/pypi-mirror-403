from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.channel import Channel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_payload import AlertPayload
    from ..models.send_notify_request_data_type_0 import SendNotifyRequestDataType0


T = TypeVar("T", bound="SendNotifyRequest")


@_attrs_define
class SendNotifyRequest:
    """Unified request to send notification via any channel.

    Attributes:
        user_id (str): Target user ID
        channel (Channel | Unset): Notification channel.
        alert (AlertPayload | None | Unset): Alert payload for push
        badge (int | None | Unset): Badge count for push
        sound (None | str | Unset): Sound name for push
        content_available (bool | Unset): Silent/background push Default: False.
        data (None | SendNotifyRequestDataType0 | Unset): Custom data payload for push
        email_subject (None | str | Unset): Email subject
        email_body_html (None | str | Unset): Email HTML body
        email_body_text (None | str | Unset): Email plain text body
        email_from (None | str | Unset): Sender email (must be @verified-domain)
    """

    user_id: str
    channel: Channel | Unset = UNSET
    alert: AlertPayload | None | Unset = UNSET
    badge: int | None | Unset = UNSET
    sound: None | str | Unset = UNSET
    content_available: bool | Unset = False
    data: None | SendNotifyRequestDataType0 | Unset = UNSET
    email_subject: None | str | Unset = UNSET
    email_body_html: None | str | Unset = UNSET
    email_body_text: None | str | Unset = UNSET
    email_from: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alert_payload import AlertPayload
        from ..models.send_notify_request_data_type_0 import SendNotifyRequestDataType0

        user_id = self.user_id

        channel: str | Unset = UNSET
        if not isinstance(self.channel, Unset):
            channel = self.channel.value

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
        elif isinstance(self.data, SendNotifyRequestDataType0):
            data = self.data.to_dict()
        else:
            data = self.data

        email_subject: None | str | Unset
        if isinstance(self.email_subject, Unset):
            email_subject = UNSET
        else:
            email_subject = self.email_subject

        email_body_html: None | str | Unset
        if isinstance(self.email_body_html, Unset):
            email_body_html = UNSET
        else:
            email_body_html = self.email_body_html

        email_body_text: None | str | Unset
        if isinstance(self.email_body_text, Unset):
            email_body_text = UNSET
        else:
            email_body_text = self.email_body_text

        email_from: None | str | Unset
        if isinstance(self.email_from, Unset):
            email_from = UNSET
        else:
            email_from = self.email_from

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
            }
        )
        if channel is not UNSET:
            field_dict["channel"] = channel
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
        if email_subject is not UNSET:
            field_dict["email_subject"] = email_subject
        if email_body_html is not UNSET:
            field_dict["email_body_html"] = email_body_html
        if email_body_text is not UNSET:
            field_dict["email_body_text"] = email_body_text
        if email_from is not UNSET:
            field_dict["email_from"] = email_from

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_payload import AlertPayload
        from ..models.send_notify_request_data_type_0 import SendNotifyRequestDataType0

        d = dict(src_dict)
        user_id = d.pop("user_id")

        _channel = d.pop("channel", UNSET)
        channel: Channel | Unset
        if isinstance(_channel, Unset):
            channel = UNSET
        else:
            channel = Channel(_channel)

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

        def _parse_data(data: object) -> None | SendNotifyRequestDataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = SendNotifyRequestDataType0.from_dict(data)

                return data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SendNotifyRequestDataType0 | Unset, data)

        data = _parse_data(d.pop("data", UNSET))

        def _parse_email_subject(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_subject = _parse_email_subject(d.pop("email_subject", UNSET))

        def _parse_email_body_html(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_body_html = _parse_email_body_html(d.pop("email_body_html", UNSET))

        def _parse_email_body_text(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_body_text = _parse_email_body_text(d.pop("email_body_text", UNSET))

        def _parse_email_from(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email_from = _parse_email_from(d.pop("email_from", UNSET))

        send_notify_request = cls(
            user_id=user_id,
            channel=channel,
            alert=alert,
            badge=badge,
            sound=sound,
            content_available=content_available,
            data=data,
            email_subject=email_subject,
            email_body_html=email_body_html,
            email_body_text=email_body_text,
            email_from=email_from,
        )

        send_notify_request.additional_properties = d
        return send_notify_request

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

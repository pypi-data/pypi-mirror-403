from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_event_type import WebhookEventType
from ..types import UNSET, Unset

T = TypeVar("T", bound="TestWebhookRequest")


@_attrs_define
class TestWebhookRequest:
    """Request to send a test webhook.

    Attributes:
        event_type (None | Unset | WebhookEventType): Event type to test with Default: WebhookEventType.USER_CREATED.
    """

    event_type: None | Unset | WebhookEventType = WebhookEventType.USER_CREATED
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_type: None | str | Unset
        if isinstance(self.event_type, Unset):
            event_type = UNSET
        elif isinstance(self.event_type, WebhookEventType):
            event_type = self.event_type.value
        else:
            event_type = self.event_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if event_type is not UNSET:
            field_dict["event_type"] = event_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_event_type(data: object) -> None | Unset | WebhookEventType:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                event_type_type_0 = WebhookEventType(data)

                return event_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | WebhookEventType, data)

        event_type = _parse_event_type(d.pop("event_type", UNSET))

        test_webhook_request = cls(
            event_type=event_type,
        )

        test_webhook_request.additional_properties = d
        return test_webhook_request

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

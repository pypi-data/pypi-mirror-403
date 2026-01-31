from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_event_type import WebhookEventType

if TYPE_CHECKING:
    from ..models.dispatch_webhook_request_payload import DispatchWebhookRequestPayload


T = TypeVar("T", bound="DispatchWebhookRequest")


@_attrs_define
class DispatchWebhookRequest:
    """Internal request to dispatch a webhook event.

    Attributes:
        app_id (str): App to dispatch event for
        event_type (WebhookEventType): Supported webhook event types.
        payload (DispatchWebhookRequestPayload): Event payload data
    """

    app_id: str
    event_type: WebhookEventType
    payload: DispatchWebhookRequestPayload
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        app_id = self.app_id

        event_type = self.event_type.value

        payload = self.payload.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "app_id": app_id,
                "event_type": event_type,
                "payload": payload,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dispatch_webhook_request_payload import DispatchWebhookRequestPayload

        d = dict(src_dict)
        app_id = d.pop("app_id")

        event_type = WebhookEventType(d.pop("event_type"))

        payload = DispatchWebhookRequestPayload.from_dict(d.pop("payload"))

        dispatch_webhook_request = cls(
            app_id=app_id,
            event_type=event_type,
            payload=payload,
        )

        dispatch_webhook_request.additional_properties = d
        return dispatch_webhook_request

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

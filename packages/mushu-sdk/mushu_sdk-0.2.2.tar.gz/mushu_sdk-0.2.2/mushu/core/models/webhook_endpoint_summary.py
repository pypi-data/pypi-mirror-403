from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_event_type import WebhookEventType

T = TypeVar("T", bound="WebhookEndpointSummary")


@_attrs_define
class WebhookEndpointSummary:
    """Webhook endpoint summary (without secret).

    Attributes:
        endpoint_id (str): Unique endpoint ID
        app_id (str): App this endpoint belongs to
        url (str): Endpoint URL
        events (list[WebhookEventType]): Events to receive
        enabled (bool): Whether endpoint is enabled
        created_at (str): When endpoint was created
    """

    endpoint_id: str
    app_id: str
    url: str
    events: list[WebhookEventType]
    enabled: bool
    created_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        endpoint_id = self.endpoint_id

        app_id = self.app_id

        url = self.url

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.value
            events.append(events_item)

        enabled = self.enabled

        created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "endpoint_id": endpoint_id,
                "app_id": app_id,
                "url": url,
                "events": events,
                "enabled": enabled,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        endpoint_id = d.pop("endpoint_id")

        app_id = d.pop("app_id")

        url = d.pop("url")

        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = WebhookEventType(events_item_data)

            events.append(events_item)

        enabled = d.pop("enabled")

        created_at = d.pop("created_at")

        webhook_endpoint_summary = cls(
            endpoint_id=endpoint_id,
            app_id=app_id,
            url=url,
            events=events,
            enabled=enabled,
            created_at=created_at,
        )

        webhook_endpoint_summary.additional_properties = d
        return webhook_endpoint_summary

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

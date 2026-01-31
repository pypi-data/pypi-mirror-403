from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.webhook_delivery_status import WebhookDeliveryStatus


T = TypeVar("T", bound="DispatchWebhookResponse")


@_attrs_define
class DispatchWebhookResponse:
    """Response from dispatching webhooks.

    Attributes:
        event_type (str): Event type dispatched
        deliveries (list[WebhookDeliveryStatus]): Delivery results
    """

    event_type: str
    deliveries: list[WebhookDeliveryStatus]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_type = self.event_type

        deliveries = []
        for deliveries_item_data in self.deliveries:
            deliveries_item = deliveries_item_data.to_dict()
            deliveries.append(deliveries_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "event_type": event_type,
                "deliveries": deliveries,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_delivery_status import WebhookDeliveryStatus

        d = dict(src_dict)
        event_type = d.pop("event_type")

        deliveries = []
        _deliveries = d.pop("deliveries")
        for deliveries_item_data in _deliveries:
            deliveries_item = WebhookDeliveryStatus.from_dict(deliveries_item_data)

            deliveries.append(deliveries_item)

        dispatch_webhook_response = cls(
            event_type=event_type,
            deliveries=deliveries,
        )

        dispatch_webhook_response.additional_properties = d
        return dispatch_webhook_response

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

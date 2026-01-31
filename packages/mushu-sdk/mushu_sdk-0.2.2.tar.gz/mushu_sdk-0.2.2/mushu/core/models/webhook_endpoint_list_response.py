from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.webhook_endpoint_summary import WebhookEndpointSummary


T = TypeVar("T", bound="WebhookEndpointListResponse")


@_attrs_define
class WebhookEndpointListResponse:
    """Response with list of webhook endpoints.

    Attributes:
        endpoints (list[WebhookEndpointSummary]):
    """

    endpoints: list[WebhookEndpointSummary]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        endpoints = []
        for endpoints_item_data in self.endpoints:
            endpoints_item = endpoints_item_data.to_dict()
            endpoints.append(endpoints_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "endpoints": endpoints,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook_endpoint_summary import WebhookEndpointSummary

        d = dict(src_dict)
        endpoints = []
        _endpoints = d.pop("endpoints")
        for endpoints_item_data in _endpoints:
            endpoints_item = WebhookEndpointSummary.from_dict(endpoints_item_data)

            endpoints.append(endpoints_item)

        webhook_endpoint_list_response = cls(
            endpoints=endpoints,
        )

        webhook_endpoint_list_response.additional_properties = d
        return webhook_endpoint_list_response

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

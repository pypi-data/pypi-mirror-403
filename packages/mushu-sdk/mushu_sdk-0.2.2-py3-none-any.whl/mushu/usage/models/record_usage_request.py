from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.record_usage_request_metadata_type_0 import RecordUsageRequestMetadataType0


T = TypeVar("T", bound="RecordUsageRequest")


@_attrs_define
class RecordUsageRequest:
    """Request to record a usage event.

    Attributes:
        org_id (str):
        app_id (str):
        service (str):
        metric (str):
        quantity (int | Unset):  Default: 1.
        metadata (None | RecordUsageRequestMetadataType0 | Unset):
    """

    org_id: str
    app_id: str
    service: str
    metric: str
    quantity: int | Unset = 1
    metadata: None | RecordUsageRequestMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.record_usage_request_metadata_type_0 import RecordUsageRequestMetadataType0

        org_id = self.org_id

        app_id = self.app_id

        service = self.service

        metric = self.metric

        quantity = self.quantity

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, RecordUsageRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "app_id": app_id,
                "service": service,
                "metric": metric,
            }
        )
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.record_usage_request_metadata_type_0 import RecordUsageRequestMetadataType0

        d = dict(src_dict)
        org_id = d.pop("org_id")

        app_id = d.pop("app_id")

        service = d.pop("service")

        metric = d.pop("metric")

        quantity = d.pop("quantity", UNSET)

        def _parse_metadata(data: object) -> None | RecordUsageRequestMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = RecordUsageRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RecordUsageRequestMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        record_usage_request = cls(
            org_id=org_id,
            app_id=app_id,
            service=service,
            metric=metric,
            quantity=quantity,
            metadata=metadata,
        )

        record_usage_request.additional_properties = d
        return record_usage_request

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

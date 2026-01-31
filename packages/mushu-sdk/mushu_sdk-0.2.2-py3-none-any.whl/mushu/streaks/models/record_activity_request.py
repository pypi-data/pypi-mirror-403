from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.record_activity_request_metadata_type_0 import RecordActivityRequestMetadataType0


T = TypeVar("T", bound="RecordActivityRequest")


@_attrs_define
class RecordActivityRequest:
    """Request to record an activity.

    Attributes:
        activity_type (str | Unset): Type of activity Default: 'default'.
        timestamp (datetime.datetime | None | Unset): Activity timestamp (defaults to now)
        timezone (str | Unset): User's timezone (e.g., America/Los_Angeles) Default: 'UTC'.
        metadata (None | RecordActivityRequestMetadataType0 | Unset): Optional metadata for the activity
    """

    activity_type: str | Unset = "default"
    timestamp: datetime.datetime | None | Unset = UNSET
    timezone: str | Unset = "UTC"
    metadata: None | RecordActivityRequestMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.record_activity_request_metadata_type_0 import (
            RecordActivityRequestMetadataType0,
        )

        activity_type = self.activity_type

        timestamp: None | str | Unset
        if isinstance(self.timestamp, Unset):
            timestamp = UNSET
        elif isinstance(self.timestamp, datetime.datetime):
            timestamp = self.timestamp.isoformat()
        else:
            timestamp = self.timestamp

        timezone = self.timezone

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, RecordActivityRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if activity_type is not UNSET:
            field_dict["activity_type"] = activity_type
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.record_activity_request_metadata_type_0 import (
            RecordActivityRequestMetadataType0,
        )

        d = dict(src_dict)
        activity_type = d.pop("activity_type", UNSET)

        def _parse_timestamp(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timestamp_type_0 = isoparse(data)

                return timestamp_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        timestamp = _parse_timestamp(d.pop("timestamp", UNSET))

        timezone = d.pop("timezone", UNSET)

        def _parse_metadata(data: object) -> None | RecordActivityRequestMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = RecordActivityRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RecordActivityRequestMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        record_activity_request = cls(
            activity_type=activity_type,
            timestamp=timestamp,
            timezone=timezone,
            metadata=metadata,
        )

        record_activity_request.additional_properties = d
        return record_activity_request

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

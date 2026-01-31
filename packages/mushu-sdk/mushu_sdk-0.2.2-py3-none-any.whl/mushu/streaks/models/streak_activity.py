from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.streak_activity_metadata_type_0 import StreakActivityMetadataType0


T = TypeVar("T", bound="StreakActivity")


@_attrs_define
class StreakActivity:
    """Individual activity record.

    Attributes:
        activity_id (str):
        activity_type (str):
        recorded_at (datetime.datetime):
        date (str): YYYY-MM-DD in user's timezone
        metadata (None | StreakActivityMetadataType0 | Unset):
    """

    activity_id: str
    activity_type: str
    recorded_at: datetime.datetime
    date: str
    metadata: None | StreakActivityMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.streak_activity_metadata_type_0 import StreakActivityMetadataType0

        activity_id = self.activity_id

        activity_type = self.activity_type

        recorded_at = self.recorded_at.isoformat()

        date = self.date

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, StreakActivityMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "activity_id": activity_id,
                "activity_type": activity_type,
                "recorded_at": recorded_at,
                "date": date,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.streak_activity_metadata_type_0 import StreakActivityMetadataType0

        d = dict(src_dict)
        activity_id = d.pop("activity_id")

        activity_type = d.pop("activity_type")

        recorded_at = isoparse(d.pop("recorded_at"))

        date = d.pop("date")

        def _parse_metadata(data: object) -> None | StreakActivityMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = StreakActivityMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | StreakActivityMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        streak_activity = cls(
            activity_id=activity_id,
            activity_type=activity_type,
            recorded_at=recorded_at,
            date=date,
            metadata=metadata,
        )

        streak_activity.additional_properties = d
        return streak_activity

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

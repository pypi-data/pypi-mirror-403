from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TimezoneResponse")


@_attrs_define
class TimezoneResponse:
    """Response with timezone information.

    Attributes:
        timezone (str): IANA timezone name (e.g., 'America/Los_Angeles')
        utc_offset_hours (float): Current UTC offset in hours
    """

    timezone: str
    utc_offset_hours: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        timezone = self.timezone

        utc_offset_hours = self.utc_offset_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timezone": timezone,
                "utc_offset_hours": utc_offset_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        timezone = d.pop("timezone")

        utc_offset_hours = d.pop("utc_offset_hours")

        timezone_response = cls(
            timezone=timezone,
            utc_offset_hours=utc_offset_hours,
        )

        timezone_response.additional_properties = d
        return timezone_response

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

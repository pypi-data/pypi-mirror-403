from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReverseGeocodeRequest")


@_attrs_define
class ReverseGeocodeRequest:
    """Request for reverse geocoding.

    Attributes:
        lat (float): Latitude in degrees
        lng (float): Longitude in degrees
        language (str | Unset): Language code Default: 'en'.
    """

    lat: float
    lng: float
    language: str | Unset = "en"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lat = self.lat

        lng = self.lng

        language = self.language

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lat": lat,
                "lng": lng,
            }
        )
        if language is not UNSET:
            field_dict["language"] = language

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lat = d.pop("lat")

        lng = d.pop("lng")

        language = d.pop("language", UNSET)

        reverse_geocode_request = cls(
            lat=lat,
            lng=lng,
            language=language,
        )

        reverse_geocode_request.additional_properties = d
        return reverse_geocode_request

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

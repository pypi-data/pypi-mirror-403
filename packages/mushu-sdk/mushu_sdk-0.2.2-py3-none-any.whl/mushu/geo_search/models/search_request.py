from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SearchRequest")


@_attrs_define
class SearchRequest:
    """
    Attributes:
        lat (float):  Example: 37.7749.
        lng (float):  Example: -122.4194.
        radius_km (float):  Example: 10.
        text (str | Unset):  Example: running.
        tags (list[str] | Unset): All tags must match (AND) Example: ['running'].
        tags_any (list[str] | Unset): Any tag must match (OR) Example: ['fitness', 'sports'].
        limit (int | Unset):  Default: 20. Example: 20.
    """

    lat: float
    lng: float
    radius_km: float
    text: str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    tags_any: list[str] | Unset = UNSET
    limit: int | Unset = 20
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lat = self.lat

        lng = self.lng

        radius_km = self.radius_km

        text = self.text

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        tags_any: list[str] | Unset = UNSET
        if not isinstance(self.tags_any, Unset):
            tags_any = self.tags_any

        limit = self.limit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lat": lat,
                "lng": lng,
                "radius_km": radius_km,
            }
        )
        if text is not UNSET:
            field_dict["text"] = text
        if tags is not UNSET:
            field_dict["tags"] = tags
        if tags_any is not UNSET:
            field_dict["tags_any"] = tags_any
        if limit is not UNSET:
            field_dict["limit"] = limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lat = d.pop("lat")

        lng = d.pop("lng")

        radius_km = d.pop("radius_km")

        text = d.pop("text", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        tags_any = cast(list[str], d.pop("tags_any", UNSET))

        limit = d.pop("limit", UNSET)

        search_request = cls(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            text=text,
            tags=tags,
            tags_any=tags_any,
            limit=limit,
        )

        search_request.additional_properties = d
        return search_request

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

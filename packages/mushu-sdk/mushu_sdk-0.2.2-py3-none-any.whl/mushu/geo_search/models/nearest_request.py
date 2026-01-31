from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NearestRequest")


@_attrs_define
class NearestRequest:
    """
    Attributes:
        lat (float):  Example: 37.7749.
        lng (float):  Example: -122.4194.
        text (str | Unset):  Example: coffee.
        tags (list[str] | Unset): All tags must match (AND) Example: ['cafe'].
        tags_any (list[str] | Unset): Any tag must match (OR) Example: ['food', 'drinks'].
        limit (int | Unset):  Default: 10. Example: 10.
    """

    lat: float
    lng: float
    text: str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    tags_any: list[str] | Unset = UNSET
    limit: int | Unset = 10
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lat = self.lat

        lng = self.lng

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

        text = d.pop("text", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        tags_any = cast(list[str], d.pop("tags_any", UNSET))

        limit = d.pop("limit", UNSET)

        nearest_request = cls(
            lat=lat,
            lng=lng,
            text=text,
            tags=tags,
            tags_any=tags_any,
            limit=limit,
        )

        nearest_request.additional_properties = d
        return nearest_request

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

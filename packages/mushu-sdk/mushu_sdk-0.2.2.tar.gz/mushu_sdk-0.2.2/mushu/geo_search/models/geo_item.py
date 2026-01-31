from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.geo_item_data import GeoItemData


T = TypeVar("T", bound="GeoItem")


@_attrs_define
class GeoItem:
    """
    Attributes:
        id (str):  Example: item-123.
        collection (str):  Example: groups.
        lat (float):  Example: 37.7749.
        lng (float):  Example: -122.4194.
        name (str | Unset):  Example: SF Running Club.
        description (str | Unset):  Example: Weekly runs in Golden Gate Park.
        tags (list[str] | Unset):  Example: ['running', 'fitness'].
        data (GeoItemData | Unset):  Example: {'members': 150}.
        distance_km (float | Unset):  Example: 2.5.
        created_at (float | Unset):  Example: 1704067200.
        updated_at (float | Unset):  Example: 1704067200.
    """

    id: str
    collection: str
    lat: float
    lng: float
    name: str | Unset = UNSET
    description: str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    data: GeoItemData | Unset = UNSET
    distance_km: float | Unset = UNSET
    created_at: float | Unset = UNSET
    updated_at: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        collection = self.collection

        lat = self.lat

        lng = self.lng

        name = self.name

        description = self.description

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        distance_km = self.distance_km

        created_at = self.created_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "collection": collection,
                "lat": lat,
                "lng": lng,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if data is not UNSET:
            field_dict["data"] = data
        if distance_km is not UNSET:
            field_dict["distance_km"] = distance_km
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.geo_item_data import GeoItemData

        d = dict(src_dict)
        id = d.pop("id")

        collection = d.pop("collection")

        lat = d.pop("lat")

        lng = d.pop("lng")

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        _data = d.pop("data", UNSET)
        data: GeoItemData | Unset
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = GeoItemData.from_dict(_data)

        distance_km = d.pop("distance_km", UNSET)

        created_at = d.pop("created_at", UNSET)

        updated_at = d.pop("updated_at", UNSET)

        geo_item = cls(
            id=id,
            collection=collection,
            lat=lat,
            lng=lng,
            name=name,
            description=description,
            tags=tags,
            data=data,
            distance_km=distance_km,
            created_at=created_at,
            updated_at=updated_at,
        )

        geo_item.additional_properties = d
        return geo_item

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.put_item_request_data import PutItemRequestData


T = TypeVar("T", bound="PutItemRequest")


@_attrs_define
class PutItemRequest:
    """
    Attributes:
        lat (float):  Example: 37.7749.
        lng (float):  Example: -122.4194.
        name (str | Unset):  Example: SF Running Club.
        description (str | Unset):  Example: Weekly runs in Golden Gate Park.
        tags (list[str] | Unset):  Example: ['running', 'fitness'].
        data (PutItemRequestData | Unset):  Example: {'members': 150}.
    """

    lat: float
    lng: float
    name: str | Unset = UNSET
    description: str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    data: PutItemRequestData | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.put_item_request_data import PutItemRequestData

        d = dict(src_dict)
        lat = d.pop("lat")

        lng = d.pop("lng")

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        tags = cast(list[str], d.pop("tags", UNSET))

        _data = d.pop("data", UNSET)
        data: PutItemRequestData | Unset
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = PutItemRequestData.from_dict(_data)

        put_item_request = cls(
            lat=lat,
            lng=lng,
            name=name,
            description=description,
            tags=tags,
            data=data,
        )

        put_item_request.additional_properties = d
        return put_item_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.put_item_response_status import PutItemResponseStatus

T = TypeVar("T", bound="PutItemResponse")


@_attrs_define
class PutItemResponse:
    """
    Attributes:
        id (str):  Example: item-123.
        collection (str):  Example: groups.
        status (PutItemResponseStatus):  Example: ok.
    """

    id: str
    collection: str
    status: PutItemResponseStatus
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        collection = self.collection

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "collection": collection,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        collection = d.pop("collection")

        status = PutItemResponseStatus(d.pop("status"))

        put_item_response = cls(
            id=id,
            collection=collection,
            status=status,
        )

        put_item_response.additional_properties = d
        return put_item_response

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

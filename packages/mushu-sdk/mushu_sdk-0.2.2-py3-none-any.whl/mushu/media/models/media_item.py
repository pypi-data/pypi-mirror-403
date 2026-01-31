from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.media_status import MediaStatus
from ..models.media_type import MediaType
from ..types import UNSET, Unset

T = TypeVar("T", bound="MediaItem")


@_attrs_define
class MediaItem:
    """Media item details.

    Attributes:
        media_id (str):
        org_id (str):
        app_id (None | str):
        filename (str):
        content_type (str):
        size_bytes (int):
        media_type (MediaType): Type of media file.
        status (MediaStatus): Status of media upload.
        key (str):
        created_at (str):
        updated_at (str):
        url (None | str | Unset):
    """

    media_id: str
    org_id: str
    app_id: None | str
    filename: str
    content_type: str
    size_bytes: int
    media_type: MediaType
    status: MediaStatus
    key: str
    created_at: str
    updated_at: str
    url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        media_id = self.media_id

        org_id = self.org_id

        app_id: None | str
        app_id = self.app_id

        filename = self.filename

        content_type = self.content_type

        size_bytes = self.size_bytes

        media_type = self.media_type.value

        status = self.status.value

        key = self.key

        created_at = self.created_at

        updated_at = self.updated_at

        url: None | str | Unset
        if isinstance(self.url, Unset):
            url = UNSET
        else:
            url = self.url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "media_id": media_id,
                "org_id": org_id,
                "app_id": app_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "media_type": media_type,
                "status": status,
                "key": key,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if url is not UNSET:
            field_dict["url"] = url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        media_id = d.pop("media_id")

        org_id = d.pop("org_id")

        def _parse_app_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        app_id = _parse_app_id(d.pop("app_id"))

        filename = d.pop("filename")

        content_type = d.pop("content_type")

        size_bytes = d.pop("size_bytes")

        media_type = MediaType(d.pop("media_type"))

        status = MediaStatus(d.pop("status"))

        key = d.pop("key")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        def _parse_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        url = _parse_url(d.pop("url", UNSET))

        media_item = cls(
            media_id=media_id,
            org_id=org_id,
            app_id=app_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            media_type=media_type,
            status=status,
            key=key,
            created_at=created_at,
            updated_at=updated_at,
            url=url,
        )

        media_item.additional_properties = d
        return media_item

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UploadUrlRequest")


@_attrs_define
class UploadUrlRequest:
    """Request to generate a presigned upload URL.

    Attributes:
        org_id (str): Organization ID
        filename (str): Original filename
        content_type (str): MIME type of the file
        size_bytes (int): File size in bytes (max 100MB)
        app_id (None | str | Unset): App ID (optional, for app-specific media)
    """

    org_id: str
    filename: str
    content_type: str
    size_bytes: int
    app_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        filename = self.filename

        content_type = self.content_type

        size_bytes = self.size_bytes

        app_id: None | str | Unset
        if isinstance(self.app_id, Unset):
            app_id = UNSET
        else:
            app_id = self.app_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org_id": org_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
            }
        )
        if app_id is not UNSET:
            field_dict["app_id"] = app_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("org_id")

        filename = d.pop("filename")

        content_type = d.pop("content_type")

        size_bytes = d.pop("size_bytes")

        def _parse_app_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        app_id = _parse_app_id(d.pop("app_id", UNSET))

        upload_url_request = cls(
            org_id=org_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            app_id=app_id,
        )

        upload_url_request.additional_properties = d
        return upload_url_request

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

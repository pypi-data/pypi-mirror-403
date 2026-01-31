from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="VideoUploadUrlResponse")


@_attrs_define
class VideoUploadUrlResponse:
    """Response with video upload URL.

    Attributes:
        media_id (str): Unique media ID
        upload_url (str): Presigned URL for upload to R2
        expires_in (int): Seconds until URL expires
        key (str): Storage key for the video
    """

    media_id: str
    upload_url: str
    expires_in: int
    key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        media_id = self.media_id

        upload_url = self.upload_url

        expires_in = self.expires_in

        key = self.key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "media_id": media_id,
                "upload_url": upload_url,
                "expires_in": expires_in,
                "key": key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        media_id = d.pop("media_id")

        upload_url = d.pop("upload_url")

        expires_in = d.pop("expires_in")

        key = d.pop("key")

        video_upload_url_response = cls(
            media_id=media_id,
            upload_url=upload_url,
            expires_in=expires_in,
            key=key,
        )

        video_upload_url_response.additional_properties = d
        return video_upload_url_response

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

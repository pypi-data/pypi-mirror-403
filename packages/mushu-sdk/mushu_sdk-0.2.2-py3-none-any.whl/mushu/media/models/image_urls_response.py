from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ImageUrlsResponse")


@_attrs_define
class ImageUrlsResponse:
    """Response with image variant URLs.

    Attributes:
        media_id (str):
        original (str): Original image URL
        thumbnail (str): 150x150 thumbnail URL
        small (str): 320px width URL
        medium (str): 640px width URL
        large (str): 1280px width URL
    """

    media_id: str
    original: str
    thumbnail: str
    small: str
    medium: str
    large: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        media_id = self.media_id

        original = self.original

        thumbnail = self.thumbnail

        small = self.small

        medium = self.medium

        large = self.large

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "media_id": media_id,
                "original": original,
                "thumbnail": thumbnail,
                "small": small,
                "medium": medium,
                "large": large,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        media_id = d.pop("media_id")

        original = d.pop("original")

        thumbnail = d.pop("thumbnail")

        small = d.pop("small")

        medium = d.pop("medium")

        large = d.pop("large")

        image_urls_response = cls(
            media_id=media_id,
            original=original,
            thumbnail=thumbnail,
            small=small,
            medium=medium,
            large=large,
        )

        image_urls_response.additional_properties = d
        return image_urls_response

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

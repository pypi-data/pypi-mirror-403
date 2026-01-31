from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.video_status import VideoStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="VideoVariantsResponse")


@_attrs_define
class VideoVariantsResponse:
    """Video variant URLs for download.

    Attributes:
        media_id (str):
        status (VideoStatus): Video processing status.
        job_id (None | str | Unset): MediaConvert job ID
        original (None | str | Unset): Original uploaded video URL
        optimized (None | str | Unset): H.264 MP4 (1080p, 8Mbps) URL
        web (None | str | Unset): VP9 WebM (1080p, 5Mbps) URL
        thumbnail (None | str | Unset): Thumbnail JPEG (640x360) URL
        poster (None | str | Unset): Poster JPEG (1280x720) URL
        error_message (None | str | Unset): Error message if status is ERROR
    """

    media_id: str
    status: VideoStatus
    job_id: None | str | Unset = UNSET
    original: None | str | Unset = UNSET
    optimized: None | str | Unset = UNSET
    web: None | str | Unset = UNSET
    thumbnail: None | str | Unset = UNSET
    poster: None | str | Unset = UNSET
    error_message: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        media_id = self.media_id

        status = self.status.value

        job_id: None | str | Unset
        if isinstance(self.job_id, Unset):
            job_id = UNSET
        else:
            job_id = self.job_id

        original: None | str | Unset
        if isinstance(self.original, Unset):
            original = UNSET
        else:
            original = self.original

        optimized: None | str | Unset
        if isinstance(self.optimized, Unset):
            optimized = UNSET
        else:
            optimized = self.optimized

        web: None | str | Unset
        if isinstance(self.web, Unset):
            web = UNSET
        else:
            web = self.web

        thumbnail: None | str | Unset
        if isinstance(self.thumbnail, Unset):
            thumbnail = UNSET
        else:
            thumbnail = self.thumbnail

        poster: None | str | Unset
        if isinstance(self.poster, Unset):
            poster = UNSET
        else:
            poster = self.poster

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "media_id": media_id,
                "status": status,
            }
        )
        if job_id is not UNSET:
            field_dict["job_id"] = job_id
        if original is not UNSET:
            field_dict["original"] = original
        if optimized is not UNSET:
            field_dict["optimized"] = optimized
        if web is not UNSET:
            field_dict["web"] = web
        if thumbnail is not UNSET:
            field_dict["thumbnail"] = thumbnail
        if poster is not UNSET:
            field_dict["poster"] = poster
        if error_message is not UNSET:
            field_dict["error_message"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        media_id = d.pop("media_id")

        status = VideoStatus(d.pop("status"))

        def _parse_job_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        job_id = _parse_job_id(d.pop("job_id", UNSET))

        def _parse_original(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        original = _parse_original(d.pop("original", UNSET))

        def _parse_optimized(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        optimized = _parse_optimized(d.pop("optimized", UNSET))

        def _parse_web(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        web = _parse_web(d.pop("web", UNSET))

        def _parse_thumbnail(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        thumbnail = _parse_thumbnail(d.pop("thumbnail", UNSET))

        def _parse_poster(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        poster = _parse_poster(d.pop("poster", UNSET))

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("error_message", UNSET))

        video_variants_response = cls(
            media_id=media_id,
            status=status,
            job_id=job_id,
            original=original,
            optimized=optimized,
            web=web,
            thumbnail=thumbnail,
            poster=poster,
            error_message=error_message,
        )

        video_variants_response.additional_properties = d
        return video_variants_response

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

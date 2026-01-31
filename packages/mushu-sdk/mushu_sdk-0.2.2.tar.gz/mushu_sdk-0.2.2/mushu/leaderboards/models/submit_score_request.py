from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.submit_score_request_metadata_type_0 import SubmitScoreRequestMetadataType0


T = TypeVar("T", bound="SubmitScoreRequest")


@_attrs_define
class SubmitScoreRequest:
    """Request to submit a score.

    Attributes:
        user_id (str): User identifier
        score (float): Score value
        metadata (None | SubmitScoreRequestMetadataType0 | Unset): Optional metadata
    """

    user_id: str
    score: float
    metadata: None | SubmitScoreRequestMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.submit_score_request_metadata_type_0 import SubmitScoreRequestMetadataType0

        user_id = self.user_id

        score = self.score

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, SubmitScoreRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "score": score,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.submit_score_request_metadata_type_0 import SubmitScoreRequestMetadataType0

        d = dict(src_dict)
        user_id = d.pop("user_id")

        score = d.pop("score")

        def _parse_metadata(data: object) -> None | SubmitScoreRequestMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = SubmitScoreRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SubmitScoreRequestMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        submit_score_request = cls(
            user_id=user_id,
            score=score,
            metadata=metadata,
        )

        submit_score_request.additional_properties = d
        return submit_score_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.submit_score_response_ranks import SubmitScoreResponseRanks


T = TypeVar("T", bound="SubmitScoreResponse")


@_attrs_define
class SubmitScoreResponse:
    """Response after submitting a score.

    Attributes:
        accepted (bool):
        entry_id (None | str | Unset):
        new_total (float | None | Unset): New total score for user
        ranks (SubmitScoreResponseRanks | Unset): User's rank per enabled time window
        rejection_reason (None | str | Unset):
    """

    accepted: bool
    entry_id: None | str | Unset = UNSET
    new_total: float | None | Unset = UNSET
    ranks: SubmitScoreResponseRanks | Unset = UNSET
    rejection_reason: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        accepted = self.accepted

        entry_id: None | str | Unset
        if isinstance(self.entry_id, Unset):
            entry_id = UNSET
        else:
            entry_id = self.entry_id

        new_total: float | None | Unset
        if isinstance(self.new_total, Unset):
            new_total = UNSET
        else:
            new_total = self.new_total

        ranks: dict[str, Any] | Unset = UNSET
        if not isinstance(self.ranks, Unset):
            ranks = self.ranks.to_dict()

        rejection_reason: None | str | Unset
        if isinstance(self.rejection_reason, Unset):
            rejection_reason = UNSET
        else:
            rejection_reason = self.rejection_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accepted": accepted,
            }
        )
        if entry_id is not UNSET:
            field_dict["entry_id"] = entry_id
        if new_total is not UNSET:
            field_dict["new_total"] = new_total
        if ranks is not UNSET:
            field_dict["ranks"] = ranks
        if rejection_reason is not UNSET:
            field_dict["rejection_reason"] = rejection_reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.submit_score_response_ranks import SubmitScoreResponseRanks

        d = dict(src_dict)
        accepted = d.pop("accepted")

        def _parse_entry_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        entry_id = _parse_entry_id(d.pop("entry_id", UNSET))

        def _parse_new_total(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        new_total = _parse_new_total(d.pop("new_total", UNSET))

        _ranks = d.pop("ranks", UNSET)
        ranks: SubmitScoreResponseRanks | Unset
        if isinstance(_ranks, Unset):
            ranks = UNSET
        else:
            ranks = SubmitScoreResponseRanks.from_dict(_ranks)

        def _parse_rejection_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        rejection_reason = _parse_rejection_reason(d.pop("rejection_reason", UNSET))

        submit_score_response = cls(
            accepted=accepted,
            entry_id=entry_id,
            new_total=new_total,
            ranks=ranks,
            rejection_reason=rejection_reason,
        )

        submit_score_response.additional_properties = d
        return submit_score_response

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

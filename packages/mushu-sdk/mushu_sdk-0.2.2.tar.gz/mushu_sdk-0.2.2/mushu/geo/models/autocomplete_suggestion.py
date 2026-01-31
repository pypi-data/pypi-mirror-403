from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.autocomplete_suggestion_context_type_0 import AutocompleteSuggestionContextType0


T = TypeVar("T", bound="AutocompleteSuggestion")


@_attrs_define
class AutocompleteSuggestion:
    """A single autocomplete suggestion.

    Attributes:
        place_name (str): Full formatted place name
        text (str): Primary text to display
        place_type (list[str] | Unset): Place types
        lat (float | None | Unset): Latitude if available
        lng (float | None | Unset): Longitude if available
        context (AutocompleteSuggestionContextType0 | None | Unset): Additional context (city, region, country)
    """

    place_name: str
    text: str
    place_type: list[str] | Unset = UNSET
    lat: float | None | Unset = UNSET
    lng: float | None | Unset = UNSET
    context: AutocompleteSuggestionContextType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.autocomplete_suggestion_context_type_0 import (
            AutocompleteSuggestionContextType0,
        )

        place_name = self.place_name

        text = self.text

        place_type: list[str] | Unset = UNSET
        if not isinstance(self.place_type, Unset):
            place_type = self.place_type

        lat: float | None | Unset
        if isinstance(self.lat, Unset):
            lat = UNSET
        else:
            lat = self.lat

        lng: float | None | Unset
        if isinstance(self.lng, Unset):
            lng = UNSET
        else:
            lng = self.lng

        context: dict[str, Any] | None | Unset
        if isinstance(self.context, Unset):
            context = UNSET
        elif isinstance(self.context, AutocompleteSuggestionContextType0):
            context = self.context.to_dict()
        else:
            context = self.context

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "place_name": place_name,
                "text": text,
            }
        )
        if place_type is not UNSET:
            field_dict["place_type"] = place_type
        if lat is not UNSET:
            field_dict["lat"] = lat
        if lng is not UNSET:
            field_dict["lng"] = lng
        if context is not UNSET:
            field_dict["context"] = context

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.autocomplete_suggestion_context_type_0 import (
            AutocompleteSuggestionContextType0,
        )

        d = dict(src_dict)
        place_name = d.pop("place_name")

        text = d.pop("text")

        place_type = cast(list[str], d.pop("place_type", UNSET))

        def _parse_lat(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        lat = _parse_lat(d.pop("lat", UNSET))

        def _parse_lng(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        lng = _parse_lng(d.pop("lng", UNSET))

        def _parse_context(data: object) -> AutocompleteSuggestionContextType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                context_type_0 = AutocompleteSuggestionContextType0.from_dict(data)

                return context_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AutocompleteSuggestionContextType0 | None | Unset, data)

        context = _parse_context(d.pop("context", UNSET))

        autocomplete_suggestion = cls(
            place_name=place_name,
            text=text,
            place_type=place_type,
            lat=lat,
            lng=lng,
            context=context,
        )

        autocomplete_suggestion.additional_properties = d
        return autocomplete_suggestion

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

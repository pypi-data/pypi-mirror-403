from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.push_status_events_body_events_item_event_window_type import PushStatusEventsBodyEventsItemEventWindowType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.push_status_events_body_events_item_event_window_actual import (
        PushStatusEventsBodyEventsItemEventWindowActual,
    )
    from ..models.push_status_events_body_events_item_event_window_expected import (
        PushStatusEventsBodyEventsItemEventWindowExpected,
    )


T = TypeVar("T", bound="PushStatusEventsBodyEventsItemEventWindow")


@_attrs_define
class PushStatusEventsBodyEventsItemEventWindow:
    """
    Attributes:
        type_ (PushStatusEventsBodyEventsItemEventWindowType | Unset):  Example: delivery.
        expected (PushStatusEventsBodyEventsItemEventWindowExpected | Unset):
        actual (PushStatusEventsBodyEventsItemEventWindowActual | Unset):
    """

    type_: PushStatusEventsBodyEventsItemEventWindowType | Unset = UNSET
    expected: PushStatusEventsBodyEventsItemEventWindowExpected | Unset = UNSET
    actual: PushStatusEventsBodyEventsItemEventWindowActual | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        expected: dict[str, Any] | Unset = UNSET
        if not isinstance(self.expected, Unset):
            expected = self.expected.to_dict()

        actual: dict[str, Any] | Unset = UNSET
        if not isinstance(self.actual, Unset):
            actual = self.actual.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if expected is not UNSET:
            field_dict["expected"] = expected
        if actual is not UNSET:
            field_dict["actual"] = actual

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.push_status_events_body_events_item_event_window_actual import (
            PushStatusEventsBodyEventsItemEventWindowActual,
        )
        from ..models.push_status_events_body_events_item_event_window_expected import (
            PushStatusEventsBodyEventsItemEventWindowExpected,
        )

        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: PushStatusEventsBodyEventsItemEventWindowType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = PushStatusEventsBodyEventsItemEventWindowType(_type_)

        _expected = d.pop("expected", UNSET)
        expected: PushStatusEventsBodyEventsItemEventWindowExpected | Unset
        if isinstance(_expected, Unset):
            expected = UNSET
        else:
            expected = PushStatusEventsBodyEventsItemEventWindowExpected.from_dict(_expected)

        _actual = d.pop("actual", UNSET)
        actual: PushStatusEventsBodyEventsItemEventWindowActual | Unset
        if isinstance(_actual, Unset):
            actual = UNSET
        else:
            actual = PushStatusEventsBodyEventsItemEventWindowActual.from_dict(_actual)

        push_status_events_body_events_item_event_window = cls(
            type_=type_,
            expected=expected,
            actual=actual,
        )

        push_status_events_body_events_item_event_window.additional_properties = d
        return push_status_events_body_events_item_event_window

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_status_response_200_events_item import GetStatusResponse200EventsItem
    from ..models.get_status_response_200_shipment import GetStatusResponse200Shipment


T = TypeVar("T", bound="GetStatusResponse200")


@_attrs_define
class GetStatusResponse200:
    """
    Attributes:
        shipment (GetStatusResponse200Shipment | Unset):
        events (list[GetStatusResponse200EventsItem] | Unset):
    """

    shipment: GetStatusResponse200Shipment | Unset = UNSET
    events: list[GetStatusResponse200EventsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment, Unset):
            shipment = self.shipment.to_dict()

        events: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.events, Unset):
            events = []
            for events_item_data in self.events:
                events_item = events_item_data.to_dict()
                events.append(events_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipment is not UNSET:
            field_dict["shipment"] = shipment
        if events is not UNSET:
            field_dict["events"] = events

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_status_response_200_events_item import GetStatusResponse200EventsItem
        from ..models.get_status_response_200_shipment import GetStatusResponse200Shipment

        d = dict(src_dict)
        _shipment = d.pop("shipment", UNSET)
        shipment: GetStatusResponse200Shipment | Unset
        if isinstance(_shipment, Unset):
            shipment = UNSET
        else:
            shipment = GetStatusResponse200Shipment.from_dict(_shipment)

        _events = d.pop("events", UNSET)
        events: list[GetStatusResponse200EventsItem] | Unset = UNSET
        if _events is not UNSET:
            events = []
            for events_item_data in _events:
                events_item = GetStatusResponse200EventsItem.from_dict(events_item_data)

                events.append(events_item)

        get_status_response_200 = cls(
            shipment=shipment,
            events=events,
        )

        get_status_response_200.additional_properties = d
        return get_status_response_200

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

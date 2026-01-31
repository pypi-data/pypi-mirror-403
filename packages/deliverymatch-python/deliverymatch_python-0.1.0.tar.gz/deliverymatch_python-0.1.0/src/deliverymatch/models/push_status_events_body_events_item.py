from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.push_status_events_body_events_item_event_window import PushStatusEventsBodyEventsItemEventWindow


T = TypeVar("T", bound="PushStatusEventsBodyEventsItem")


@_attrs_define
class PushStatusEventsBodyEventsItem:
    """
    Attributes:
        tracking_number (str): Awb/barcode Example: DM91.
        status_code (str):  Example: DELIVERED.
        description (str):  Example: Shipment has been delivered.
        date (datetime.datetime): Date when the event has occured Example: 2025-03-13 12:34:56.
        city (str | Unset):  Example: Capelle aan den IJssel.
        postal_code (str | Unset):  Example: 2909 LK.
        country (str | Unset):  Example: NL.
        latitude (str | Unset):  Example: 51.9137894.
        longitude (str | Unset):  Example: 4.5433589.
        delivery_window (datetime.datetime | Unset):  Example: 2025-03-13 12:34:56.
        accepted_by (str | Unset):  Example: Roland Slegers.
        remark (str | Unset):  Example: note.
        event_window (PushStatusEventsBodyEventsItemEventWindow | Unset):
    """

    tracking_number: str
    status_code: str
    description: str
    date: datetime.datetime
    city: str | Unset = UNSET
    postal_code: str | Unset = UNSET
    country: str | Unset = UNSET
    latitude: str | Unset = UNSET
    longitude: str | Unset = UNSET
    delivery_window: datetime.datetime | Unset = UNSET
    accepted_by: str | Unset = UNSET
    remark: str | Unset = UNSET
    event_window: PushStatusEventsBodyEventsItemEventWindow | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tracking_number = self.tracking_number

        status_code = self.status_code

        description = self.description

        date = self.date.isoformat()

        city = self.city

        postal_code = self.postal_code

        country = self.country

        latitude = self.latitude

        longitude = self.longitude

        delivery_window: str | Unset = UNSET
        if not isinstance(self.delivery_window, Unset):
            delivery_window = self.delivery_window.isoformat()

        accepted_by = self.accepted_by

        remark = self.remark

        event_window: dict[str, Any] | Unset = UNSET
        if not isinstance(self.event_window, Unset):
            event_window = self.event_window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trackingNumber": tracking_number,
                "statusCode": status_code,
                "description": description,
                "date": date,
            }
        )
        if city is not UNSET:
            field_dict["city"] = city
        if postal_code is not UNSET:
            field_dict["postalCode"] = postal_code
        if country is not UNSET:
            field_dict["country"] = country
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if delivery_window is not UNSET:
            field_dict["deliveryWindow"] = delivery_window
        if accepted_by is not UNSET:
            field_dict["acceptedBy"] = accepted_by
        if remark is not UNSET:
            field_dict["remark"] = remark
        if event_window is not UNSET:
            field_dict["eventWindow"] = event_window

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.push_status_events_body_events_item_event_window import PushStatusEventsBodyEventsItemEventWindow

        d = dict(src_dict)
        tracking_number = d.pop("trackingNumber")

        status_code = d.pop("statusCode")

        description = d.pop("description")

        date = isoparse(d.pop("date"))

        city = d.pop("city", UNSET)

        postal_code = d.pop("postalCode", UNSET)

        country = d.pop("country", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        _delivery_window = d.pop("deliveryWindow", UNSET)
        delivery_window: datetime.datetime | Unset
        if isinstance(_delivery_window, Unset):
            delivery_window = UNSET
        else:
            delivery_window = isoparse(_delivery_window)

        accepted_by = d.pop("acceptedBy", UNSET)

        remark = d.pop("remark", UNSET)

        _event_window = d.pop("eventWindow", UNSET)
        event_window: PushStatusEventsBodyEventsItemEventWindow | Unset
        if isinstance(_event_window, Unset):
            event_window = UNSET
        else:
            event_window = PushStatusEventsBodyEventsItemEventWindow.from_dict(_event_window)

        push_status_events_body_events_item = cls(
            tracking_number=tracking_number,
            status_code=status_code,
            description=description,
            date=date,
            city=city,
            postal_code=postal_code,
            country=country,
            latitude=latitude,
            longitude=longitude,
            delivery_window=delivery_window,
            accepted_by=accepted_by,
            remark=remark,
            event_window=event_window,
        )

        push_status_events_body_events_item.additional_properties = d
        return push_status_events_body_events_item

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

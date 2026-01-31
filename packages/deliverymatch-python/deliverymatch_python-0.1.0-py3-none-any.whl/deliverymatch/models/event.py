from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Event")


@_attrs_define
class Event:
    """Status details per events of requested shipments

    Attributes:
        shipment_id (int | Unset):
        tracking_number (str | Unset):
        main_status (str | Unset):
        event_date (str | Unset):
        code (str | Unset):
        description (str | Unset):
        city (str | Unset):
        postal_code (str | Unset):
        country (str | Unset):
        latitude (float | Unset):
        longitude (float | Unset):
        accepted_by (str | Unset):
    """

    shipment_id: int | Unset = UNSET
    tracking_number: str | Unset = UNSET
    main_status: str | Unset = UNSET
    event_date: str | Unset = UNSET
    code: str | Unset = UNSET
    description: str | Unset = UNSET
    city: str | Unset = UNSET
    postal_code: str | Unset = UNSET
    country: str | Unset = UNSET
    latitude: float | Unset = UNSET
    longitude: float | Unset = UNSET
    accepted_by: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment_id = self.shipment_id

        tracking_number = self.tracking_number

        main_status = self.main_status

        event_date = self.event_date

        code = self.code

        description = self.description

        city = self.city

        postal_code = self.postal_code

        country = self.country

        latitude = self.latitude

        longitude = self.longitude

        accepted_by = self.accepted_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipment_id is not UNSET:
            field_dict["shipmentId"] = shipment_id
        if tracking_number is not UNSET:
            field_dict["trackingNumber"] = tracking_number
        if main_status is not UNSET:
            field_dict["mainStatus"] = main_status
        if event_date is not UNSET:
            field_dict["eventDate"] = event_date
        if code is not UNSET:
            field_dict["code"] = code
        if description is not UNSET:
            field_dict["description"] = description
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
        if accepted_by is not UNSET:
            field_dict["acceptedBy"] = accepted_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        shipment_id = d.pop("shipmentId", UNSET)

        tracking_number = d.pop("trackingNumber", UNSET)

        main_status = d.pop("mainStatus", UNSET)

        event_date = d.pop("eventDate", UNSET)

        code = d.pop("code", UNSET)

        description = d.pop("description", UNSET)

        city = d.pop("city", UNSET)

        postal_code = d.pop("postalCode", UNSET)

        country = d.pop("country", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        accepted_by = d.pop("acceptedBy", UNSET)

        event = cls(
            shipment_id=shipment_id,
            tracking_number=tracking_number,
            main_status=main_status,
            event_date=event_date,
            code=code,
            description=description,
            city=city,
            postal_code=postal_code,
            country=country,
            latitude=latitude,
            longitude=longitude,
            accepted_by=accepted_by,
        )

        event.additional_properties = d
        return event

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

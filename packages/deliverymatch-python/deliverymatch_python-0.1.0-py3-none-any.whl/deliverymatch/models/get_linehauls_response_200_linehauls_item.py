from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLinehaulsResponse200LinehaulsItem")


@_attrs_define
class GetLinehaulsResponse200LinehaulsItem:
    """
    Attributes:
        id (str | Unset):
        shipments (int | Unset):
        channel (str | Unset):
        carrier (str | Unset):
        service (str | Unset):
        country (str | Unset):
        lastupdate (str | Unset):
        closed (bool | Unset):
    """

    id: str | Unset = UNSET
    shipments: int | Unset = UNSET
    channel: str | Unset = UNSET
    carrier: str | Unset = UNSET
    service: str | Unset = UNSET
    country: str | Unset = UNSET
    lastupdate: str | Unset = UNSET
    closed: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        shipments = self.shipments

        channel = self.channel

        carrier = self.carrier

        service = self.service

        country = self.country

        lastupdate = self.lastupdate

        closed = self.closed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if shipments is not UNSET:
            field_dict["shipments"] = shipments
        if channel is not UNSET:
            field_dict["channel"] = channel
        if carrier is not UNSET:
            field_dict["carrier"] = carrier
        if service is not UNSET:
            field_dict["service"] = service
        if country is not UNSET:
            field_dict["country"] = country
        if lastupdate is not UNSET:
            field_dict["lastupdate"] = lastupdate
        if closed is not UNSET:
            field_dict["closed"] = closed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        shipments = d.pop("shipments", UNSET)

        channel = d.pop("channel", UNSET)

        carrier = d.pop("carrier", UNSET)

        service = d.pop("service", UNSET)

        country = d.pop("country", UNSET)

        lastupdate = d.pop("lastupdate", UNSET)

        closed = d.pop("closed", UNSET)

        get_linehauls_response_200_linehauls_item = cls(
            id=id,
            shipments=shipments,
            channel=channel,
            carrier=carrier,
            service=service,
            country=country,
            lastupdate=lastupdate,
            closed=closed,
        )

        get_linehauls_response_200_linehauls_item.additional_properties = d
        return get_linehauls_response_200_linehauls_item

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

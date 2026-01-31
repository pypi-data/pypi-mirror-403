from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRoutesBodyFilter")


@_attrs_define
class UpdateRoutesBodyFilter:
    """The filters to apply

    Attributes:
        carrier (int): ID of the carrier Example: 123.
        service (int | Unset): ID of the service level Example: 123.
        country (str | Unset): 2 character ISO country code.

            **Note**: when using 2 characters, it also takes the configurations with zones. E.g. "country": "NL" will also
            include NL10, NL11 etc. "country": "NL11" uses only NL11. Example: NL10.
        day (int | Unset): Day of the week (ranging between 1-7) Example: 3.
        time_from (str | Unset):  Example: 08:00.
        time_to (str | Unset):  Example: 18:00.
    """

    carrier: int
    service: int | Unset = UNSET
    country: str | Unset = UNSET
    day: int | Unset = UNSET
    time_from: str | Unset = UNSET
    time_to: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        carrier = self.carrier

        service = self.service

        country = self.country

        day = self.day

        time_from = self.time_from

        time_to = self.time_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "carrier": carrier,
            }
        )
        if service is not UNSET:
            field_dict["service"] = service
        if country is not UNSET:
            field_dict["country"] = country
        if day is not UNSET:
            field_dict["day"] = day
        if time_from is not UNSET:
            field_dict["timeFrom"] = time_from
        if time_to is not UNSET:
            field_dict["timeTo"] = time_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        carrier = d.pop("carrier")

        service = d.pop("service", UNSET)

        country = d.pop("country", UNSET)

        day = d.pop("day", UNSET)

        time_from = d.pop("timeFrom", UNSET)

        time_to = d.pop("timeTo", UNSET)

        update_routes_body_filter = cls(
            carrier=carrier,
            service=service,
            country=country,
            day=day,
            time_from=time_from,
            time_to=time_to,
        )

        update_routes_body_filter.additional_properties = d
        return update_routes_body_filter

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

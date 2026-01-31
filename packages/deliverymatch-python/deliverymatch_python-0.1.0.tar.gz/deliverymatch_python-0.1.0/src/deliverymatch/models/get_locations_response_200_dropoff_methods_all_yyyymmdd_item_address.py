from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress")


@_attrs_define
class GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress:
    """
    Attributes:
        street (str | Unset):
        number (str | Unset):
        city (str | Unset):
        country (str | Unset):
        postcode (str | Unset):
    """

    street: str | Unset = UNSET
    number: str | Unset = UNSET
    city: str | Unset = UNSET
    country: str | Unset = UNSET
    postcode: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        street = self.street

        number = self.number

        city = self.city

        country = self.country

        postcode = self.postcode

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if street is not UNSET:
            field_dict["street"] = street
        if number is not UNSET:
            field_dict["number"] = number
        if city is not UNSET:
            field_dict["city"] = city
        if country is not UNSET:
            field_dict["country"] = country
        if postcode is not UNSET:
            field_dict["postcode"] = postcode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        street = d.pop("street", UNSET)

        number = d.pop("number", UNSET)

        city = d.pop("city", UNSET)

        country = d.pop("country", UNSET)

        postcode = d.pop("postcode", UNSET)

        get_locations_response_200_dropoff_methods_all_yyyymmdd_item_address = cls(
            street=street,
            number=number,
            city=city,
            country=country,
            postcode=postcode,
        )

        get_locations_response_200_dropoff_methods_all_yyyymmdd_item_address.additional_properties = d
        return get_locations_response_200_dropoff_methods_all_yyyymmdd_item_address

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLocationsBodyAddress")


@_attrs_define
class GetLocationsBodyAddress:
    """Address used to find dropoff locations

    Attributes:
        address1 (str): Full address line, including street, housenumber and extention (when available) Example: Rivium
            Boulevard 201-223.
        city (str): Name of the city/town Example: Capelle a/d Ijssel.
        country (str): Two character code of the country (ISO 3166-1 alpha-2) Example: NL.
        postcode (str | Unset): Postal code/zipcode Example: 2909LK.
    """

    address1: str
    city: str
    country: str
    postcode: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address1 = self.address1

        city = self.city

        country = self.country

        postcode = self.postcode

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address1": address1,
                "city": city,
                "country": country,
            }
        )
        if postcode is not UNSET:
            field_dict["postcode"] = postcode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address1 = d.pop("address1")

        city = d.pop("city")

        country = d.pop("country")

        postcode = d.pop("postcode", UNSET)

        get_locations_body_address = cls(
            address1=address1,
            city=city,
            country=country,
            postcode=postcode,
        )

        get_locations_body_address.additional_properties = d
        return get_locations_body_address

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

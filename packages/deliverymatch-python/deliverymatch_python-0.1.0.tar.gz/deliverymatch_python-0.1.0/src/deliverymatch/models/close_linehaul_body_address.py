from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CloseLinehaulBodyAddress")


@_attrs_define
class CloseLinehaulBodyAddress:
    """
    Attributes:
        name (str | Unset): Full name of the receiver Example: Roland Slegers.
        company_name (str | Unset): Name of the receiver's company Example: DeliveryMatch.
        address1 (str | Unset): Street name and housenumber of the receiver Example: Rivium Boulevard 201-223.
        street (str | Unset): Streetname of the receiver Example: Rivium Boulevard.
        house_nr (str | Unset): Housenumber of the receiver (excluding extension) Example: 201-223.
        house_nr_ext (str | Unset): Extension of the receiver's housenumber
        postcode (str | Unset): Postalcode of the receiver Example: 2909LK.
        city (str | Unset): City of the receiver Example: Capelle a/d Ijsel.
        country (str | Unset): ISO 2 country code of the receiver Example: NL.
    """

    name: str | Unset = UNSET
    company_name: str | Unset = UNSET
    address1: str | Unset = UNSET
    street: str | Unset = UNSET
    house_nr: str | Unset = UNSET
    house_nr_ext: str | Unset = UNSET
    postcode: str | Unset = UNSET
    city: str | Unset = UNSET
    country: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        company_name = self.company_name

        address1 = self.address1

        street = self.street

        house_nr = self.house_nr

        house_nr_ext = self.house_nr_ext

        postcode = self.postcode

        city = self.city

        country = self.country

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if company_name is not UNSET:
            field_dict["companyName"] = company_name
        if address1 is not UNSET:
            field_dict["address1"] = address1
        if street is not UNSET:
            field_dict["street"] = street
        if house_nr is not UNSET:
            field_dict["houseNr"] = house_nr
        if house_nr_ext is not UNSET:
            field_dict["houseNrExt"] = house_nr_ext
        if postcode is not UNSET:
            field_dict["postcode"] = postcode
        if city is not UNSET:
            field_dict["city"] = city
        if country is not UNSET:
            field_dict["country"] = country

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        company_name = d.pop("companyName", UNSET)

        address1 = d.pop("address1", UNSET)

        street = d.pop("street", UNSET)

        house_nr = d.pop("houseNr", UNSET)

        house_nr_ext = d.pop("houseNrExt", UNSET)

        postcode = d.pop("postcode", UNSET)

        city = d.pop("city", UNSET)

        country = d.pop("country", UNSET)

        close_linehaul_body_address = cls(
            name=name,
            company_name=company_name,
            address1=address1,
            street=street,
            house_nr=house_nr,
            house_nr_ext=house_nr_ext,
            postcode=postcode,
            city=city,
            country=country,
        )

        close_linehaul_body_address.additional_properties = d
        return close_linehaul_body_address

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

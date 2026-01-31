from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Address")


@_attrs_define
class Address:
    """General address information of a given individual

    Attributes:
        name (str): Name of the person Example: Roland Slegers.
        address1 (str): Full address line, including street, housenumber and extention (when available) Example: Rivium
            Boulevard 201-223.
        street (str): Street name Example: Rivium Boulevard.
        house_nr (int): Housenumber (excluding extention) Example: 201-223.
        postcode (str): Postal code/zipcode Example: 2909LK.
        city (str): Name of the city/town Example: Capelle a/d Ijssel.
        country (str): Two character code of the country (ISO 3166-1 alpha-2) Example: NL.
        company_name (str | Unset): Name of the company Example: DeliveryMatch.
        address2 (str | Unset): Other additional address information Example: Second floor.
        house_nr_ext (str | Unset): Housenumber extension
        state (str | Unset): Two character code of the state Example: UT.
        zone (str | Unset): Indication of a zone/region for internal usage. Will appear as a label in the shipment
            overview
    """

    name: str
    address1: str
    street: str
    house_nr: int
    postcode: str
    city: str
    country: str
    company_name: str | Unset = UNSET
    address2: str | Unset = UNSET
    house_nr_ext: str | Unset = UNSET
    state: str | Unset = UNSET
    zone: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        address1 = self.address1

        street = self.street

        house_nr = self.house_nr

        postcode = self.postcode

        city = self.city

        country = self.country

        company_name = self.company_name

        address2 = self.address2

        house_nr_ext = self.house_nr_ext

        state = self.state

        zone = self.zone

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "address1": address1,
                "street": street,
                "houseNr": house_nr,
                "postcode": postcode,
                "city": city,
                "country": country,
            }
        )
        if company_name is not UNSET:
            field_dict["companyName"] = company_name
        if address2 is not UNSET:
            field_dict["address2"] = address2
        if house_nr_ext is not UNSET:
            field_dict["houseNrExt"] = house_nr_ext
        if state is not UNSET:
            field_dict["state"] = state
        if zone is not UNSET:
            field_dict["zone"] = zone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        address1 = d.pop("address1")

        street = d.pop("street")

        house_nr = d.pop("houseNr")

        postcode = d.pop("postcode")

        city = d.pop("city")

        country = d.pop("country")

        company_name = d.pop("companyName", UNSET)

        address2 = d.pop("address2", UNSET)

        house_nr_ext = d.pop("houseNrExt", UNSET)

        state = d.pop("state", UNSET)

        zone = d.pop("zone", UNSET)

        address = cls(
            name=name,
            address1=address1,
            street=street,
            house_nr=house_nr,
            postcode=postcode,
            city=city,
            country=country,
            company_name=company_name,
            address2=address2,
            house_nr_ext=house_nr_ext,
            state=state,
            zone=zone,
        )

        address.additional_properties = d
        return address

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

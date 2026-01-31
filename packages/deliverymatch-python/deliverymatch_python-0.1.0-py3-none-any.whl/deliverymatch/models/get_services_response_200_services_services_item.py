from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_services_response_200_services_services_item_countries_item import (
        GetServicesResponse200ServicesServicesItemCountriesItem,
    )


T = TypeVar("T", bound="GetServicesResponse200ServicesServicesItem")


@_attrs_define
class GetServicesResponse200ServicesServicesItem:
    """
    Attributes:
        carrier (str | Unset):
        carrier_id (float | Unset):
        service (str | Unset):
        service_id (float | Unset):
        description (str | Unset):
        countries (list[GetServicesResponse200ServicesServicesItemCountriesItem] | Unset):
    """

    carrier: str | Unset = UNSET
    carrier_id: float | Unset = UNSET
    service: str | Unset = UNSET
    service_id: float | Unset = UNSET
    description: str | Unset = UNSET
    countries: list[GetServicesResponse200ServicesServicesItemCountriesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        carrier = self.carrier

        carrier_id = self.carrier_id

        service = self.service

        service_id = self.service_id

        description = self.description

        countries: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.countries, Unset):
            countries = []
            for countries_item_data in self.countries:
                countries_item = countries_item_data.to_dict()
                countries.append(countries_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if carrier is not UNSET:
            field_dict["carrier"] = carrier
        if carrier_id is not UNSET:
            field_dict["carrierID"] = carrier_id
        if service is not UNSET:
            field_dict["service"] = service
        if service_id is not UNSET:
            field_dict["serviceID"] = service_id
        if description is not UNSET:
            field_dict["description"] = description
        if countries is not UNSET:
            field_dict["countries"] = countries

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_services_response_200_services_services_item_countries_item import (
            GetServicesResponse200ServicesServicesItemCountriesItem,
        )

        d = dict(src_dict)
        carrier = d.pop("carrier", UNSET)

        carrier_id = d.pop("carrierID", UNSET)

        service = d.pop("service", UNSET)

        service_id = d.pop("serviceID", UNSET)

        description = d.pop("description", UNSET)

        _countries = d.pop("countries", UNSET)
        countries: list[GetServicesResponse200ServicesServicesItemCountriesItem] | Unset = UNSET
        if _countries is not UNSET:
            countries = []
            for countries_item_data in _countries:
                countries_item = GetServicesResponse200ServicesServicesItemCountriesItem.from_dict(countries_item_data)

                countries.append(countries_item)

        get_services_response_200_services_services_item = cls(
            carrier=carrier,
            carrier_id=carrier_id,
            service=service,
            service_id=service_id,
            description=description,
            countries=countries,
        )

        get_services_response_200_services_services_item.additional_properties = d
        return get_services_response_200_services_services_item

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

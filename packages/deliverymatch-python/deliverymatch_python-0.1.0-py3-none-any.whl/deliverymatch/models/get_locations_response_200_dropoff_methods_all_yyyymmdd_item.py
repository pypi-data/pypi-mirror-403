from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_address import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_carrier import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemCarrier,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_service_level import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemServiceLevel,
    )


T = TypeVar("T", bound="GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem")


@_attrs_define
class GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem:
    """
    Attributes:
        id (str | Unset):
        name (str | Unset):
        address (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress | Unset):
        openinghours (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours | Unset):
        phonenumber (str | Unset):
        longitude (float | Unset):
        latitude (float | Unset):
        network (float | Unset):
        network_loc_id (str | Unset):
        carrier (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemCarrier | Unset):
        service_level (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemServiceLevel | Unset):
        distance (float | Unset):
        network_name (str | Unset):
        price (float | Unset):
        configuration_id (float | Unset):
        tariff_id (float | Unset):
        check_id (str | Unset):
        method_id (str | Unset):
        date_pickup (str | Unset):
        pickup_time (str | Unset):
        cutoff_time (str | Unset):
        date_delivery (str | Unset):
        time_from (str | Unset):
        time_to (str | Unset):
    """

    id: str | Unset = UNSET
    name: str | Unset = UNSET
    address: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress | Unset = UNSET
    openinghours: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours | Unset = UNSET
    phonenumber: str | Unset = UNSET
    longitude: float | Unset = UNSET
    latitude: float | Unset = UNSET
    network: float | Unset = UNSET
    network_loc_id: str | Unset = UNSET
    carrier: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemCarrier | Unset = UNSET
    service_level: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemServiceLevel | Unset = UNSET
    distance: float | Unset = UNSET
    network_name: str | Unset = UNSET
    price: float | Unset = UNSET
    configuration_id: float | Unset = UNSET
    tariff_id: float | Unset = UNSET
    check_id: str | Unset = UNSET
    method_id: str | Unset = UNSET
    date_pickup: str | Unset = UNSET
    pickup_time: str | Unset = UNSET
    cutoff_time: str | Unset = UNSET
    date_delivery: str | Unset = UNSET
    time_from: str | Unset = UNSET
    time_to: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        address: dict[str, Any] | Unset = UNSET
        if not isinstance(self.address, Unset):
            address = self.address.to_dict()

        openinghours: dict[str, Any] | Unset = UNSET
        if not isinstance(self.openinghours, Unset):
            openinghours = self.openinghours.to_dict()

        phonenumber = self.phonenumber

        longitude = self.longitude

        latitude = self.latitude

        network = self.network

        network_loc_id = self.network_loc_id

        carrier: dict[str, Any] | Unset = UNSET
        if not isinstance(self.carrier, Unset):
            carrier = self.carrier.to_dict()

        service_level: dict[str, Any] | Unset = UNSET
        if not isinstance(self.service_level, Unset):
            service_level = self.service_level.to_dict()

        distance = self.distance

        network_name = self.network_name

        price = self.price

        configuration_id = self.configuration_id

        tariff_id = self.tariff_id

        check_id = self.check_id

        method_id = self.method_id

        date_pickup = self.date_pickup

        pickup_time = self.pickup_time

        cutoff_time = self.cutoff_time

        date_delivery = self.date_delivery

        time_from = self.time_from

        time_to = self.time_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if address is not UNSET:
            field_dict["address"] = address
        if openinghours is not UNSET:
            field_dict["openinghours"] = openinghours
        if phonenumber is not UNSET:
            field_dict["phonenumber"] = phonenumber
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if network is not UNSET:
            field_dict["network"] = network
        if network_loc_id is not UNSET:
            field_dict["network_loc_id"] = network_loc_id
        if carrier is not UNSET:
            field_dict["carrier"] = carrier
        if service_level is not UNSET:
            field_dict["serviceLevel"] = service_level
        if distance is not UNSET:
            field_dict["distance"] = distance
        if network_name is not UNSET:
            field_dict["network_name"] = network_name
        if price is not UNSET:
            field_dict["price"] = price
        if configuration_id is not UNSET:
            field_dict["configurationID"] = configuration_id
        if tariff_id is not UNSET:
            field_dict["tariffID"] = tariff_id
        if check_id is not UNSET:
            field_dict["checkID"] = check_id
        if method_id is not UNSET:
            field_dict["methodID"] = method_id
        if date_pickup is not UNSET:
            field_dict["datePickup"] = date_pickup
        if pickup_time is not UNSET:
            field_dict["pickupTime"] = pickup_time
        if cutoff_time is not UNSET:
            field_dict["cutoffTime"] = cutoff_time
        if date_delivery is not UNSET:
            field_dict["dateDelivery"] = date_delivery
        if time_from is not UNSET:
            field_dict["timeFrom"] = time_from
        if time_to is not UNSET:
            field_dict["timeTo"] = time_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_address import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_carrier import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemCarrier,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_service_level import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemServiceLevel,
        )

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        _address = d.pop("address", UNSET)
        address: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress | Unset
        if isinstance(_address, Unset):
            address = UNSET
        else:
            address = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemAddress.from_dict(_address)

        _openinghours = d.pop("openinghours", UNSET)
        openinghours: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours | Unset
        if isinstance(_openinghours, Unset):
            openinghours = UNSET
        else:
            openinghours = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours.from_dict(_openinghours)

        phonenumber = d.pop("phonenumber", UNSET)

        longitude = d.pop("longitude", UNSET)

        latitude = d.pop("latitude", UNSET)

        network = d.pop("network", UNSET)

        network_loc_id = d.pop("network_loc_id", UNSET)

        _carrier = d.pop("carrier", UNSET)
        carrier: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemCarrier | Unset
        if isinstance(_carrier, Unset):
            carrier = UNSET
        else:
            carrier = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemCarrier.from_dict(_carrier)

        _service_level = d.pop("serviceLevel", UNSET)
        service_level: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemServiceLevel | Unset
        if isinstance(_service_level, Unset):
            service_level = UNSET
        else:
            service_level = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemServiceLevel.from_dict(_service_level)

        distance = d.pop("distance", UNSET)

        network_name = d.pop("network_name", UNSET)

        price = d.pop("price", UNSET)

        configuration_id = d.pop("configurationID", UNSET)

        tariff_id = d.pop("tariffID", UNSET)

        check_id = d.pop("checkID", UNSET)

        method_id = d.pop("methodID", UNSET)

        date_pickup = d.pop("datePickup", UNSET)

        pickup_time = d.pop("pickupTime", UNSET)

        cutoff_time = d.pop("cutoffTime", UNSET)

        date_delivery = d.pop("dateDelivery", UNSET)

        time_from = d.pop("timeFrom", UNSET)

        time_to = d.pop("timeTo", UNSET)

        get_locations_response_200_dropoff_methods_all_yyyymmdd_item = cls(
            id=id,
            name=name,
            address=address,
            openinghours=openinghours,
            phonenumber=phonenumber,
            longitude=longitude,
            latitude=latitude,
            network=network,
            network_loc_id=network_loc_id,
            carrier=carrier,
            service_level=service_level,
            distance=distance,
            network_name=network_name,
            price=price,
            configuration_id=configuration_id,
            tariff_id=tariff_id,
            check_id=check_id,
            method_id=method_id,
            date_pickup=date_pickup,
            pickup_time=pickup_time,
            cutoff_time=cutoff_time,
            date_delivery=date_delivery,
            time_from=time_from,
            time_to=time_to,
        )

        get_locations_response_200_dropoff_methods_all_yyyymmdd_item.additional_properties = d
        return get_locations_response_200_dropoff_methods_all_yyyymmdd_item

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

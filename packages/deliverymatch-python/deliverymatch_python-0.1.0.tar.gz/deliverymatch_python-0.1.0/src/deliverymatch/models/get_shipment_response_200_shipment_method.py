from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetShipmentResponse200ShipmentMethod")


@_attrs_define
class GetShipmentResponse200ShipmentMethod:
    """
    Attributes:
        configuration_id (float | Unset):
        tariff_id (str | Unset):
        carrier_name (str | Unset):
        service_level (str | Unset):
        date_pickup (str | Unset):
        date_delivery (str | Unset):
        buy_price (float | Unset):
        sell_price (float | Unset):
        time_from (str | Unset):
        time_to (str | Unset):
        barcode (str | Unset):
        tracking_url (str | Unset):
    """

    configuration_id: float | Unset = UNSET
    tariff_id: str | Unset = UNSET
    carrier_name: str | Unset = UNSET
    service_level: str | Unset = UNSET
    date_pickup: str | Unset = UNSET
    date_delivery: str | Unset = UNSET
    buy_price: float | Unset = UNSET
    sell_price: float | Unset = UNSET
    time_from: str | Unset = UNSET
    time_to: str | Unset = UNSET
    barcode: str | Unset = UNSET
    tracking_url: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        configuration_id = self.configuration_id

        tariff_id = self.tariff_id

        carrier_name = self.carrier_name

        service_level = self.service_level

        date_pickup = self.date_pickup

        date_delivery = self.date_delivery

        buy_price = self.buy_price

        sell_price = self.sell_price

        time_from = self.time_from

        time_to = self.time_to

        barcode = self.barcode

        tracking_url = self.tracking_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if configuration_id is not UNSET:
            field_dict["configurationID"] = configuration_id
        if tariff_id is not UNSET:
            field_dict["tariffID"] = tariff_id
        if carrier_name is not UNSET:
            field_dict["carrierName"] = carrier_name
        if service_level is not UNSET:
            field_dict["serviceLevel"] = service_level
        if date_pickup is not UNSET:
            field_dict["datePickup"] = date_pickup
        if date_delivery is not UNSET:
            field_dict["dateDelivery"] = date_delivery
        if buy_price is not UNSET:
            field_dict["buy_price"] = buy_price
        if sell_price is not UNSET:
            field_dict["sell_price"] = sell_price
        if time_from is not UNSET:
            field_dict["timeFrom"] = time_from
        if time_to is not UNSET:
            field_dict["timeTo"] = time_to
        if barcode is not UNSET:
            field_dict["barcode"] = barcode
        if tracking_url is not UNSET:
            field_dict["trackingURL"] = tracking_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        configuration_id = d.pop("configurationID", UNSET)

        tariff_id = d.pop("tariffID", UNSET)

        carrier_name = d.pop("carrierName", UNSET)

        service_level = d.pop("serviceLevel", UNSET)

        date_pickup = d.pop("datePickup", UNSET)

        date_delivery = d.pop("dateDelivery", UNSET)

        buy_price = d.pop("buy_price", UNSET)

        sell_price = d.pop("sell_price", UNSET)

        time_from = d.pop("timeFrom", UNSET)

        time_to = d.pop("timeTo", UNSET)

        barcode = d.pop("barcode", UNSET)

        tracking_url = d.pop("trackingURL", UNSET)

        get_shipment_response_200_shipment_method = cls(
            configuration_id=configuration_id,
            tariff_id=tariff_id,
            carrier_name=carrier_name,
            service_level=service_level,
            date_pickup=date_pickup,
            date_delivery=date_delivery,
            buy_price=buy_price,
            sell_price=sell_price,
            time_from=time_from,
            time_to=time_to,
            barcode=barcode,
            tracking_url=tracking_url,
        )

        get_shipment_response_200_shipment_method.additional_properties = d
        return get_shipment_response_200_shipment_method

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

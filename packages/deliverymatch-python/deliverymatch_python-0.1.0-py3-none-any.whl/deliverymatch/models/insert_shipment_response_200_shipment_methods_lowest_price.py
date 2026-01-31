from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InsertShipmentResponse200ShipmentMethodsLowestPrice")


@_attrs_define
class InsertShipmentResponse200ShipmentMethodsLowestPrice:
    """
    Attributes:
        price (float | Unset):
        buy_price (float | Unset):
        currency (str | Unset):
        description (str | Unset):
        title (str | Unset):
        time_from (str | Unset):
        time_to (str | Unset):
    """

    price: float | Unset = UNSET
    buy_price: float | Unset = UNSET
    currency: str | Unset = UNSET
    description: str | Unset = UNSET
    title: str | Unset = UNSET
    time_from: str | Unset = UNSET
    time_to: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        price = self.price

        buy_price = self.buy_price

        currency = self.currency

        description = self.description

        title = self.title

        time_from = self.time_from

        time_to = self.time_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if price is not UNSET:
            field_dict["price"] = price
        if buy_price is not UNSET:
            field_dict["buy_price"] = buy_price
        if currency is not UNSET:
            field_dict["currency"] = currency
        if description is not UNSET:
            field_dict["description"] = description
        if title is not UNSET:
            field_dict["title"] = title
        if time_from is not UNSET:
            field_dict["timeFrom"] = time_from
        if time_to is not UNSET:
            field_dict["timeTo"] = time_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        price = d.pop("price", UNSET)

        buy_price = d.pop("buy_price", UNSET)

        currency = d.pop("currency", UNSET)

        description = d.pop("description", UNSET)

        title = d.pop("title", UNSET)

        time_from = d.pop("timeFrom", UNSET)

        time_to = d.pop("timeTo", UNSET)

        insert_shipment_response_200_shipment_methods_lowest_price = cls(
            price=price,
            buy_price=buy_price,
            currency=currency,
            description=description,
            title=title,
            time_from=time_from,
            time_to=time_to,
        )

        insert_shipment_response_200_shipment_methods_lowest_price.additional_properties = d
        return insert_shipment_response_200_shipment_methods_lowest_price

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

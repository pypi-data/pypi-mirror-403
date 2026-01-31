from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InsertShipmentsResponse200ShipmentsItemShipmentMethods")


@_attrs_define
class InsertShipmentsResponse200ShipmentsItemShipmentMethods:
    """
    Attributes:
        lowest_price (bool | Unset):
    """

    lowest_price: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lowest_price = self.lowest_price

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if lowest_price is not UNSET:
            field_dict["lowestPrice"] = lowest_price

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lowest_price = d.pop("lowestPrice", UNSET)

        insert_shipments_response_200_shipments_item_shipment_methods = cls(
            lowest_price=lowest_price,
        )

        insert_shipments_response_200_shipments_item_shipment_methods.additional_properties = d
        return insert_shipments_response_200_shipments_item_shipment_methods

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

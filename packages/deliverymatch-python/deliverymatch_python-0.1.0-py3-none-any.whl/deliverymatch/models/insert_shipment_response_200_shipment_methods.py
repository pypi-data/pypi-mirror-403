from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_shipment_response_200_shipment_methods_all_item import (
        InsertShipmentResponse200ShipmentMethodsAllItem,
    )
    from ..models.insert_shipment_response_200_shipment_methods_earliest import (
        InsertShipmentResponse200ShipmentMethodsEarliest,
    )
    from ..models.insert_shipment_response_200_shipment_methods_lowest_price import (
        InsertShipmentResponse200ShipmentMethodsLowestPrice,
    )


T = TypeVar("T", bound="InsertShipmentResponse200ShipmentMethods")


@_attrs_define
class InsertShipmentResponse200ShipmentMethods:
    """
    Attributes:
        lowest_price (InsertShipmentResponse200ShipmentMethodsLowestPrice | Unset):
        earliest (InsertShipmentResponse200ShipmentMethodsEarliest | Unset):
        all_ (list[InsertShipmentResponse200ShipmentMethodsAllItem] | Unset):
    """

    lowest_price: InsertShipmentResponse200ShipmentMethodsLowestPrice | Unset = UNSET
    earliest: InsertShipmentResponse200ShipmentMethodsEarliest | Unset = UNSET
    all_: list[InsertShipmentResponse200ShipmentMethodsAllItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lowest_price: dict[str, Any] | Unset = UNSET
        if not isinstance(self.lowest_price, Unset):
            lowest_price = self.lowest_price.to_dict()

        earliest: dict[str, Any] | Unset = UNSET
        if not isinstance(self.earliest, Unset):
            earliest = self.earliest.to_dict()

        all_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.all_, Unset):
            all_ = []
            for all_item_data in self.all_:
                all_item = all_item_data.to_dict()
                all_.append(all_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if lowest_price is not UNSET:
            field_dict["lowestPrice"] = lowest_price
        if earliest is not UNSET:
            field_dict["earliest"] = earliest
        if all_ is not UNSET:
            field_dict["all"] = all_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.insert_shipment_response_200_shipment_methods_all_item import (
            InsertShipmentResponse200ShipmentMethodsAllItem,
        )
        from ..models.insert_shipment_response_200_shipment_methods_earliest import (
            InsertShipmentResponse200ShipmentMethodsEarliest,
        )
        from ..models.insert_shipment_response_200_shipment_methods_lowest_price import (
            InsertShipmentResponse200ShipmentMethodsLowestPrice,
        )

        d = dict(src_dict)
        _lowest_price = d.pop("lowestPrice", UNSET)
        lowest_price: InsertShipmentResponse200ShipmentMethodsLowestPrice | Unset
        if isinstance(_lowest_price, Unset):
            lowest_price = UNSET
        else:
            lowest_price = InsertShipmentResponse200ShipmentMethodsLowestPrice.from_dict(_lowest_price)

        _earliest = d.pop("earliest", UNSET)
        earliest: InsertShipmentResponse200ShipmentMethodsEarliest | Unset
        if isinstance(_earliest, Unset):
            earliest = UNSET
        else:
            earliest = InsertShipmentResponse200ShipmentMethodsEarliest.from_dict(_earliest)

        _all_ = d.pop("all", UNSET)
        all_: list[InsertShipmentResponse200ShipmentMethodsAllItem] | Unset = UNSET
        if _all_ is not UNSET:
            all_ = []
            for all_item_data in _all_:
                all_item = InsertShipmentResponse200ShipmentMethodsAllItem.from_dict(all_item_data)

                all_.append(all_item)

        insert_shipment_response_200_shipment_methods = cls(
            lowest_price=lowest_price,
            earliest=earliest,
            all_=all_,
        )

        insert_shipment_response_200_shipment_methods.additional_properties = d
        return insert_shipment_response_200_shipment_methods

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

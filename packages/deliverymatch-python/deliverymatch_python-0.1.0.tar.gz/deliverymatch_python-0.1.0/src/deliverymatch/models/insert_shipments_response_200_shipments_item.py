from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_shipments_response_200_shipments_item_items_item import (
        InsertShipmentsResponse200ShipmentsItemItemsItem,
    )
    from ..models.insert_shipments_response_200_shipments_item_shipment_methods import (
        InsertShipmentsResponse200ShipmentsItemShipmentMethods,
    )


T = TypeVar("T", bound="InsertShipmentsResponse200ShipmentsItem")


@_attrs_define
class InsertShipmentsResponse200ShipmentsItem:
    """
    Attributes:
        location (int | Unset):
        items (list[InsertShipmentsResponse200ShipmentsItemItemsItem] | Unset):
        shipment_id (int | Unset):
        shipment_methods (InsertShipmentsResponse200ShipmentsItemShipmentMethods | Unset):
    """

    location: int | Unset = UNSET
    items: list[InsertShipmentsResponse200ShipmentsItemItemsItem] | Unset = UNSET
    shipment_id: int | Unset = UNSET
    shipment_methods: InsertShipmentsResponse200ShipmentsItemShipmentMethods | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        location = self.location

        items: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        shipment_id = self.shipment_id

        shipment_methods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment_methods, Unset):
            shipment_methods = self.shipment_methods.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if location is not UNSET:
            field_dict["location"] = location
        if items is not UNSET:
            field_dict["items"] = items
        if shipment_id is not UNSET:
            field_dict["shipmentID"] = shipment_id
        if shipment_methods is not UNSET:
            field_dict["shipmentMethods"] = shipment_methods

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.insert_shipments_response_200_shipments_item_items_item import (
            InsertShipmentsResponse200ShipmentsItemItemsItem,
        )
        from ..models.insert_shipments_response_200_shipments_item_shipment_methods import (
            InsertShipmentsResponse200ShipmentsItemShipmentMethods,
        )

        d = dict(src_dict)
        location = d.pop("location", UNSET)

        _items = d.pop("items", UNSET)
        items: list[InsertShipmentsResponse200ShipmentsItemItemsItem] | Unset = UNSET
        if _items is not UNSET:
            items = []
            for items_item_data in _items:
                items_item = InsertShipmentsResponse200ShipmentsItemItemsItem.from_dict(items_item_data)

                items.append(items_item)

        shipment_id = d.pop("shipmentID", UNSET)

        _shipment_methods = d.pop("shipmentMethods", UNSET)
        shipment_methods: InsertShipmentsResponse200ShipmentsItemShipmentMethods | Unset
        if isinstance(_shipment_methods, Unset):
            shipment_methods = UNSET
        else:
            shipment_methods = InsertShipmentsResponse200ShipmentsItemShipmentMethods.from_dict(_shipment_methods)

        insert_shipments_response_200_shipments_item = cls(
            location=location,
            items=items,
            shipment_id=shipment_id,
            shipment_methods=shipment_methods,
        )

        insert_shipments_response_200_shipments_item.additional_properties = d
        return insert_shipments_response_200_shipments_item

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InsertShipmentsResponse200ShipmentsItemItemsItem")


@_attrs_define
class InsertShipmentsResponse200ShipmentsItemItemsItem:
    """
    Attributes:
        warehouse (str | Unset):
        description (str | Unset):
        content (str | Unset):
        quantity (int | Unset):
        value (int | Unset):
        length (int | Unset):
        width (int | Unset):
        height (int | Unset):
        weight (float | Unset):
        sku (str | Unset):
        ean (str | Unset):
    """

    warehouse: str | Unset = UNSET
    description: str | Unset = UNSET
    content: str | Unset = UNSET
    quantity: int | Unset = UNSET
    value: int | Unset = UNSET
    length: int | Unset = UNSET
    width: int | Unset = UNSET
    height: int | Unset = UNSET
    weight: float | Unset = UNSET
    sku: str | Unset = UNSET
    ean: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        warehouse = self.warehouse

        description = self.description

        content = self.content

        quantity = self.quantity

        value = self.value

        length = self.length

        width = self.width

        height = self.height

        weight = self.weight

        sku = self.sku

        ean = self.ean

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if warehouse is not UNSET:
            field_dict["warehouse"] = warehouse
        if description is not UNSET:
            field_dict["description"] = description
        if content is not UNSET:
            field_dict["content"] = content
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if value is not UNSET:
            field_dict["value"] = value
        if length is not UNSET:
            field_dict["length"] = length
        if width is not UNSET:
            field_dict["width"] = width
        if height is not UNSET:
            field_dict["height"] = height
        if weight is not UNSET:
            field_dict["weight"] = weight
        if sku is not UNSET:
            field_dict["SKU"] = sku
        if ean is not UNSET:
            field_dict["EAN"] = ean

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        warehouse = d.pop("warehouse", UNSET)

        description = d.pop("description", UNSET)

        content = d.pop("content", UNSET)

        quantity = d.pop("quantity", UNSET)

        value = d.pop("value", UNSET)

        length = d.pop("length", UNSET)

        width = d.pop("width", UNSET)

        height = d.pop("height", UNSET)

        weight = d.pop("weight", UNSET)

        sku = d.pop("SKU", UNSET)

        ean = d.pop("EAN", UNSET)

        insert_shipments_response_200_shipments_item_items_item = cls(
            warehouse=warehouse,
            description=description,
            content=content,
            quantity=quantity,
            value=value,
            length=length,
            width=width,
            height=height,
            weight=weight,
            sku=sku,
            ean=ean,
        )

        insert_shipments_response_200_shipments_item_items_item.additional_properties = d
        return insert_shipments_response_200_shipments_item_items_item

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

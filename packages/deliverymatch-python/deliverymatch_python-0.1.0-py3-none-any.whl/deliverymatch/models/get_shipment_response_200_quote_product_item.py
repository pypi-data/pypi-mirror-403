from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetShipmentResponse200QuoteProductItem")


@_attrs_define
class GetShipmentResponse200QuoteProductItem:
    """
    Attributes:
        id (float | Unset):
        warehouse (str | Unset):
        description (str | Unset):
        content (str | Unset):
        quantity (float | Unset):
        value (float | Unset):
        length (float | Unset):
        width (float | Unset):
        height (float | Unset):
        weight (float | Unset):
        sku (str | Unset):
        hs_code (str | Unset):
        country_of_origin (str | Unset):
    """

    id: float | Unset = UNSET
    warehouse: str | Unset = UNSET
    description: str | Unset = UNSET
    content: str | Unset = UNSET
    quantity: float | Unset = UNSET
    value: float | Unset = UNSET
    length: float | Unset = UNSET
    width: float | Unset = UNSET
    height: float | Unset = UNSET
    weight: float | Unset = UNSET
    sku: str | Unset = UNSET
    hs_code: str | Unset = UNSET
    country_of_origin: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

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

        hs_code = self.hs_code

        country_of_origin = self.country_of_origin

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
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
        if hs_code is not UNSET:
            field_dict["hsCode"] = hs_code
        if country_of_origin is not UNSET:
            field_dict["countryOfOrigin"] = country_of_origin

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

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

        hs_code = d.pop("hsCode", UNSET)

        country_of_origin = d.pop("countryOfOrigin", UNSET)

        get_shipment_response_200_quote_product_item = cls(
            id=id,
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
            hs_code=hs_code,
            country_of_origin=country_of_origin,
        )

        get_shipment_response_200_quote_product_item.additional_properties = d
        return get_shipment_response_200_quote_product_item

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

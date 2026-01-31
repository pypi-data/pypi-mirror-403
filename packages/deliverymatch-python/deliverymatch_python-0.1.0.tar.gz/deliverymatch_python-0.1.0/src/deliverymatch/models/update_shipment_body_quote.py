from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.product import Product


T = TypeVar("T", bound="UpdateShipmentBodyQuote")


@_attrs_define
class UpdateShipmentBodyQuote:
    """Information about the items in the shipment

    Attributes:
        product (list[Product] | Unset):
    """

    product: list[Product] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        product: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.product, Unset):
            product = []
            for product_item_data in self.product:
                product_item = product_item_data.to_dict()
                product.append(product_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if product is not UNSET:
            field_dict["product"] = product

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.product import Product

        d = dict(src_dict)
        _product = d.pop("product", UNSET)
        product: list[Product] | Unset = UNSET
        if _product is not UNSET:
            product = []
            for product_item_data in _product:
                product_item = Product.from_dict(product_item_data)

                product.append(product_item)

        update_shipment_body_quote = cls(
            product=product,
        )

        update_shipment_body_quote.additional_properties = d
        return update_shipment_body_quote

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

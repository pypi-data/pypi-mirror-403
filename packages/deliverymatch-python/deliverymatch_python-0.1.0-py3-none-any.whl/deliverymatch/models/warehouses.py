from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Warehouses")


@_attrs_define
class Warehouses:
    """
    Attributes:
        id (str | Unset): Number of the warehouse, as it is added in DeliveryMatch. (For example 2 for Warehouse 2)
            Example: 2.
        stockdate (str | Unset): Date the product is available in this warehouse Example: 2022-09-04.
    """

    id: str | Unset = UNSET
    stockdate: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        stockdate = self.stockdate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if stockdate is not UNSET:
            field_dict["stockdate"] = stockdate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        stockdate = d.pop("stockdate", UNSET)

        warehouses = cls(
            id=id,
            stockdate=stockdate,
        )

        warehouses.additional_properties = d
        return warehouses

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

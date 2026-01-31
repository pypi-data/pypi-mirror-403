from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetShipmentResponse200PackagesPackageItem")


@_attrs_define
class GetShipmentResponse200PackagesPackageItem:
    """
    Attributes:
        id (float | Unset):
        warehouse (str | Unset):
        description (str | Unset):
        length (float | Unset):
        width (float | Unset):
        height (float | Unset):
        weight (float | Unset):
    """

    id: float | Unset = UNSET
    warehouse: str | Unset = UNSET
    description: str | Unset = UNSET
    length: float | Unset = UNSET
    width: float | Unset = UNSET
    height: float | Unset = UNSET
    weight: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        warehouse = self.warehouse

        description = self.description

        length = self.length

        width = self.width

        height = self.height

        weight = self.weight

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if warehouse is not UNSET:
            field_dict["warehouse"] = warehouse
        if description is not UNSET:
            field_dict["description"] = description
        if length is not UNSET:
            field_dict["length"] = length
        if width is not UNSET:
            field_dict["width"] = width
        if height is not UNSET:
            field_dict["height"] = height
        if weight is not UNSET:
            field_dict["weight"] = weight

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        warehouse = d.pop("warehouse", UNSET)

        description = d.pop("description", UNSET)

        length = d.pop("length", UNSET)

        width = d.pop("width", UNSET)

        height = d.pop("height", UNSET)

        weight = d.pop("weight", UNSET)

        get_shipment_response_200_packages_package_item = cls(
            id=id,
            warehouse=warehouse,
            description=description,
            length=length,
            width=width,
            height=height,
            weight=weight,
        )

        get_shipment_response_200_packages_package_item.additional_properties = d
        return get_shipment_response_200_packages_package_item

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

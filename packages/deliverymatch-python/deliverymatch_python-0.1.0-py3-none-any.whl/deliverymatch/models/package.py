from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Package")


@_attrs_define
class Package:
    """
    Attributes:
        warehouse (int | Unset): Number of the warehouse, as it is added in DeliveryMatch Default: 1. Example: 2.
        description (str | Unset): Short description of the contents of the package Example: Electronic goods.
        type_ (str | Unset): Type of packaging or shipping equipment Example: europallet.
        weight (float | Unset): Weight of the package in kilograms Example: 10.55.
        length (float | Unset): Length of the package in centimeters Example: 30.
        width (float | Unset): Width of the package in centimeters Example: 25.
        height (float | Unset): Height of the package in centimeters Example: 15.
        package_num (float | Unset):  Example: 1.
        dry_ice_weight (float | Unset): Dry ice weight of the package available for special service levels Default: 0.0.
            Example: 10.
        stackable (bool | Unset):  Default: False.
    """

    warehouse: int | Unset = 1
    description: str | Unset = UNSET
    type_: str | Unset = UNSET
    weight: float | Unset = UNSET
    length: float | Unset = UNSET
    width: float | Unset = UNSET
    height: float | Unset = UNSET
    package_num: float | Unset = UNSET
    dry_ice_weight: float | Unset = 0.0
    stackable: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        warehouse = self.warehouse

        description = self.description

        type_ = self.type_

        weight = self.weight

        length = self.length

        width = self.width

        height = self.height

        package_num = self.package_num

        dry_ice_weight = self.dry_ice_weight

        stackable = self.stackable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if warehouse is not UNSET:
            field_dict["warehouse"] = warehouse
        if description is not UNSET:
            field_dict["description"] = description
        if type_ is not UNSET:
            field_dict["type"] = type_
        if weight is not UNSET:
            field_dict["weight"] = weight
        if length is not UNSET:
            field_dict["length"] = length
        if width is not UNSET:
            field_dict["width"] = width
        if height is not UNSET:
            field_dict["height"] = height
        if package_num is not UNSET:
            field_dict["packageNum"] = package_num
        if dry_ice_weight is not UNSET:
            field_dict["dryIceWeight"] = dry_ice_weight
        if stackable is not UNSET:
            field_dict["stackable"] = stackable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        warehouse = d.pop("warehouse", UNSET)

        description = d.pop("description", UNSET)

        type_ = d.pop("type", UNSET)

        weight = d.pop("weight", UNSET)

        length = d.pop("length", UNSET)

        width = d.pop("width", UNSET)

        height = d.pop("height", UNSET)

        package_num = d.pop("packageNum", UNSET)

        dry_ice_weight = d.pop("dryIceWeight", UNSET)

        stackable = d.pop("stackable", UNSET)

        package = cls(
            warehouse=warehouse,
            description=description,
            type_=type_,
            weight=weight,
            length=length,
            width=width,
            height=height,
            package_num=package_num,
            dry_ice_weight=dry_ice_weight,
            stackable=stackable,
        )

        package.additional_properties = d
        return package

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateRoutesBodyAdjustment")


@_attrs_define
class UpdateRoutesBodyAdjustment:
    """Atleast one adjustment field is required

    Attributes:
        capacity (float | Unset): Capacity of the shipment Example: 20.
        capacity_cbm (float | Unset): CBM (Cubic Meter) capacity of the shipment. Also known as the freight volume of
            the shipment for domestic and international freight. This measurement is calculated by multiplying the width,
            height and length together of the shipment. Example: 0.75.
    """

    capacity: float | Unset = UNSET
    capacity_cbm: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        capacity = self.capacity

        capacity_cbm = self.capacity_cbm

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if capacity is not UNSET:
            field_dict["capacity"] = capacity
        if capacity_cbm is not UNSET:
            field_dict["capacityCBM"] = capacity_cbm

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        capacity = d.pop("capacity", UNSET)

        capacity_cbm = d.pop("capacityCBM", UNSET)

        update_routes_body_adjustment = cls(
            capacity=capacity,
            capacity_cbm=capacity_cbm,
        )

        update_routes_body_adjustment.additional_properties = d
        return update_routes_body_adjustment

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetDesignResponse200DesignActive")


@_attrs_define
class GetDesignResponse200DesignActive:
    """
    Attributes:
        delivery (bool | Unset):
        dropoff (bool | Unset):
        pickup (bool | Unset):
    """

    delivery: bool | Unset = UNSET
    dropoff: bool | Unset = UNSET
    pickup: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        delivery = self.delivery

        dropoff = self.dropoff

        pickup = self.pickup

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if delivery is not UNSET:
            field_dict["delivery"] = delivery
        if dropoff is not UNSET:
            field_dict["dropoff"] = dropoff
        if pickup is not UNSET:
            field_dict["pickup"] = pickup

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        delivery = d.pop("delivery", UNSET)

        dropoff = d.pop("dropoff", UNSET)

        pickup = d.pop("pickup", UNSET)

        get_design_response_200_design_active = cls(
            delivery=delivery,
            dropoff=dropoff,
            pickup=pickup,
        )

        get_design_response_200_design_active.additional_properties = d
        return get_design_response_200_design_active

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

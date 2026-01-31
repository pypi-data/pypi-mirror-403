from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_shipment_response_200_dropoff_methods_all_item import (
        InsertShipmentResponse200DropoffMethodsAllItem,
    )


T = TypeVar("T", bound="InsertShipmentResponse200DropoffMethods")


@_attrs_define
class InsertShipmentResponse200DropoffMethods:
    """
    Attributes:
        all_ (list[InsertShipmentResponse200DropoffMethodsAllItem] | Unset):
    """

    all_: list[InsertShipmentResponse200DropoffMethodsAllItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        all_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.all_, Unset):
            all_ = []
            for all_item_data in self.all_:
                all_item = all_item_data.to_dict()
                all_.append(all_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if all_ is not UNSET:
            field_dict["all"] = all_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.insert_shipment_response_200_dropoff_methods_all_item import (
            InsertShipmentResponse200DropoffMethodsAllItem,
        )

        d = dict(src_dict)
        _all_ = d.pop("all", UNSET)
        all_: list[InsertShipmentResponse200DropoffMethodsAllItem] | Unset = UNSET
        if _all_ is not UNSET:
            all_ = []
            for all_item_data in _all_:
                all_item = InsertShipmentResponse200DropoffMethodsAllItem.from_dict(all_item_data)

                all_.append(all_item)

        insert_shipment_response_200_dropoff_methods = cls(
            all_=all_,
        )

        insert_shipment_response_200_dropoff_methods.additional_properties = d
        return insert_shipment_response_200_dropoff_methods

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

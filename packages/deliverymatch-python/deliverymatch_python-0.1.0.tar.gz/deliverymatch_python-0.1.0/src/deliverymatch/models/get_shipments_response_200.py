from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_shipments_response_200_shipments_item import GetShipmentsResponse200ShipmentsItem


T = TypeVar("T", bound="GetShipmentsResponse200")


@_attrs_define
class GetShipmentsResponse200:
    """
    Attributes:
        shipments (list[GetShipmentsResponse200ShipmentsItem] | Unset):
    """

    shipments: list[GetShipmentsResponse200ShipmentsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.shipments, Unset):
            shipments = []
            for shipments_item_data in self.shipments:
                shipments_item = shipments_item_data.to_dict()
                shipments.append(shipments_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipments is not UNSET:
            field_dict["shipments"] = shipments

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_shipments_response_200_shipments_item import GetShipmentsResponse200ShipmentsItem

        d = dict(src_dict)
        _shipments = d.pop("shipments", UNSET)
        shipments: list[GetShipmentsResponse200ShipmentsItem] | Unset = UNSET
        if _shipments is not UNSET:
            shipments = []
            for shipments_item_data in _shipments:
                shipments_item = GetShipmentsResponse200ShipmentsItem.from_dict(shipments_item_data)

                shipments.append(shipments_item)

        get_shipments_response_200 = cls(
            shipments=shipments,
        )

        get_shipments_response_200.additional_properties = d
        return get_shipments_response_200

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.close_linehaul_body_address import CloseLinehaulBodyAddress


T = TypeVar("T", bound="CloseLinehaulBody")


@_attrs_define
class CloseLinehaulBody:
    """
    Attributes:
        linehaul_id (str): The ID of the linehaul which refers to the process of transporting goods over long distances
            using different modes of transportation Example: 123.
        container_type (str): The type of container used for the shipment. Can be "PLL or "RLC" Example: PLL.
        container_amount (int):  Example: 5.
        container_length (float | Unset):  Example: 120.
        container_width (float | Unset):  Example: 120.
        container_height (float | Unset):  Example: 120.
        address (CloseLinehaulBodyAddress | Unset):
    """

    linehaul_id: str
    container_type: str
    container_amount: int
    container_length: float | Unset = UNSET
    container_width: float | Unset = UNSET
    container_height: float | Unset = UNSET
    address: CloseLinehaulBodyAddress | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        linehaul_id = self.linehaul_id

        container_type = self.container_type

        container_amount = self.container_amount

        container_length = self.container_length

        container_width = self.container_width

        container_height = self.container_height

        address: dict[str, Any] | Unset = UNSET
        if not isinstance(self.address, Unset):
            address = self.address.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "linehaulID": linehaul_id,
                "containerType": container_type,
                "containerAmount": container_amount,
            }
        )
        if container_length is not UNSET:
            field_dict["containerLength"] = container_length
        if container_width is not UNSET:
            field_dict["containerWidth"] = container_width
        if container_height is not UNSET:
            field_dict["containerHeight"] = container_height
        if address is not UNSET:
            field_dict["address"] = address

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.close_linehaul_body_address import CloseLinehaulBodyAddress

        d = dict(src_dict)
        linehaul_id = d.pop("linehaulID")

        container_type = d.pop("containerType")

        container_amount = d.pop("containerAmount")

        container_length = d.pop("containerLength", UNSET)

        container_width = d.pop("containerWidth", UNSET)

        container_height = d.pop("containerHeight", UNSET)

        _address = d.pop("address", UNSET)
        address: CloseLinehaulBodyAddress | Unset
        if isinstance(_address, Unset):
            address = UNSET
        else:
            address = CloseLinehaulBodyAddress.from_dict(_address)

        close_linehaul_body = cls(
            linehaul_id=linehaul_id,
            container_type=container_type,
            container_amount=container_amount,
            container_length=container_length,
            container_width=container_width,
            container_height=container_height,
            address=address,
        )

        close_linehaul_body.additional_properties = d
        return close_linehaul_body

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.reference import Reference


T = TypeVar("T", bound="GetShipmentBody")


@_attrs_define
class GetShipmentBody:
    """
    Attributes:
        shipment (Reference): Reference a shipment given at least one of the following identifiers
    """

    shipment: Reference
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment = self.shipment.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shipment": shipment,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reference import Reference

        d = dict(src_dict)
        shipment = Reference.from_dict(d.pop("shipment"))

        get_shipment_body = cls(
            shipment=shipment,
        )

        get_shipment_body.additional_properties = d
        return get_shipment_body

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

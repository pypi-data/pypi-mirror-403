from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.get_locations_body_address import GetLocationsBodyAddress
    from ..models.reference import Reference


T = TypeVar("T", bound="GetLocationsBody")


@_attrs_define
class GetLocationsBody:
    """
    Attributes:
        shipment (Reference): Reference a shipment given at least one of the following identifiers
        address (GetLocationsBodyAddress): Address used to find dropoff locations
    """

    shipment: Reference
    address: GetLocationsBodyAddress
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment = self.shipment.to_dict()

        address = self.address.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "shipment": shipment,
                "address": address,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_locations_body_address import GetLocationsBodyAddress
        from ..models.reference import Reference

        d = dict(src_dict)
        shipment = Reference.from_dict(d.pop("shipment"))

        address = GetLocationsBodyAddress.from_dict(d.pop("address"))

        get_locations_body = cls(
            shipment=shipment,
            address=address,
        )

        get_locations_body.additional_properties = d
        return get_locations_body

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

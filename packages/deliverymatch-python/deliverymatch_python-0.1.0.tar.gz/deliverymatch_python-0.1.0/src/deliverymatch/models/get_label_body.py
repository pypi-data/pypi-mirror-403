from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.reference import Reference


T = TypeVar("T", bound="GetLabelBody")


@_attrs_define
class GetLabelBody:
    """
    Attributes:
        shipment (Reference | Unset): Reference a shipment given at least one of the following identifiers
        sequence (int | Unset): Sequence number of the package/label, used if one label per request is needed
        end_of_shipment (bool | Unset): Used in combination with ‘sequence’. If set to true, the requested amount of
            labels is used as the final amount of labels for the shipment Default: False.
    """

    shipment: Reference | Unset = UNSET
    sequence: int | Unset = UNSET
    end_of_shipment: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment, Unset):
            shipment = self.shipment.to_dict()

        sequence = self.sequence

        end_of_shipment = self.end_of_shipment

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipment is not UNSET:
            field_dict["shipment"] = shipment
        if sequence is not UNSET:
            field_dict["sequence"] = sequence
        if end_of_shipment is not UNSET:
            field_dict["endOfShipment"] = end_of_shipment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reference import Reference

        d = dict(src_dict)
        _shipment = d.pop("shipment", UNSET)
        shipment: Reference | Unset
        if isinstance(_shipment, Unset):
            shipment = UNSET
        else:
            shipment = Reference.from_dict(_shipment)

        sequence = d.pop("sequence", UNSET)

        end_of_shipment = d.pop("endOfShipment", UNSET)

        get_label_body = cls(
            shipment=shipment,
            sequence=sequence,
            end_of_shipment=end_of_shipment,
        )

        get_label_body.additional_properties = d
        return get_label_body

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

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_shipment_method_body_action import UpdateShipmentMethodBodyAction
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.method import Method
    from ..models.reference import Reference


T = TypeVar("T", bound="UpdateShipmentMethodBody")


@_attrs_define
class UpdateShipmentMethodBody:
    """
    Attributes:
        shipment (Reference | Unset): Reference a shipment given at least one of the following identifiers
        shipment_method (Method | Unset):
        action (UpdateShipmentMethodBodyAction | Unset): The book action books the shipment and returns the label using
            the provided callback URL with insertShipment
    """

    shipment: Reference | Unset = UNSET
    shipment_method: Method | Unset = UNSET
    action: UpdateShipmentMethodBodyAction | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment, Unset):
            shipment = self.shipment.to_dict()

        shipment_method: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment_method, Unset):
            shipment_method = self.shipment_method.to_dict()

        action: str | Unset = UNSET
        if not isinstance(self.action, Unset):
            action = self.action.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipment is not UNSET:
            field_dict["shipment"] = shipment
        if shipment_method is not UNSET:
            field_dict["shipmentMethod"] = shipment_method
        if action is not UNSET:
            field_dict["action"] = action

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.method import Method
        from ..models.reference import Reference

        d = dict(src_dict)
        _shipment = d.pop("shipment", UNSET)
        shipment: Reference | Unset
        if isinstance(_shipment, Unset):
            shipment = UNSET
        else:
            shipment = Reference.from_dict(_shipment)

        _shipment_method = d.pop("shipmentMethod", UNSET)
        shipment_method: Method | Unset
        if isinstance(_shipment_method, Unset):
            shipment_method = UNSET
        else:
            shipment_method = Method.from_dict(_shipment_method)

        _action = d.pop("action", UNSET)
        action: UpdateShipmentMethodBodyAction | Unset
        if isinstance(_action, Unset):
            action = UNSET
        else:
            action = UpdateShipmentMethodBodyAction(_action)

        update_shipment_method_body = cls(
            shipment=shipment,
            shipment_method=shipment_method,
            action=action,
        )

        update_shipment_method_body.additional_properties = d
        return update_shipment_method_body

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

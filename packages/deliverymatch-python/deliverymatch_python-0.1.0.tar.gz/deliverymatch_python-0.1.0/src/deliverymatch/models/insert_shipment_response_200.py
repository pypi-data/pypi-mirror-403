from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.insert_shipment_response_200_dropoff_methods import InsertShipmentResponse200DropoffMethods
    from ..models.insert_shipment_response_200_pickup_methods import InsertShipmentResponse200PickupMethods
    from ..models.insert_shipment_response_200_shipment_methods import InsertShipmentResponse200ShipmentMethods


T = TypeVar("T", bound="InsertShipmentResponse200")


@_attrs_define
class InsertShipmentResponse200:
    """
    Attributes:
        status (str | Unset):
        code (float | Unset):
        message (str | Unset):
        shipment_id (float | Unset):
        shipment_methods (InsertShipmentResponse200ShipmentMethods | Unset):
        dropoff_methods (InsertShipmentResponse200DropoffMethods | Unset):
        pickup_methods (InsertShipmentResponse200PickupMethods | Unset):
        field_ (str | Unset):
    """

    status: str | Unset = UNSET
    code: float | Unset = UNSET
    message: str | Unset = UNSET
    shipment_id: float | Unset = UNSET
    shipment_methods: InsertShipmentResponse200ShipmentMethods | Unset = UNSET
    dropoff_methods: InsertShipmentResponse200DropoffMethods | Unset = UNSET
    pickup_methods: InsertShipmentResponse200PickupMethods | Unset = UNSET
    field_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        code = self.code

        message = self.message

        shipment_id = self.shipment_id

        shipment_methods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shipment_methods, Unset):
            shipment_methods = self.shipment_methods.to_dict()

        dropoff_methods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dropoff_methods, Unset):
            dropoff_methods = self.dropoff_methods.to_dict()

        pickup_methods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pickup_methods, Unset):
            pickup_methods = self.pickup_methods.to_dict()

        field_ = self.field_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if code is not UNSET:
            field_dict["code"] = code
        if message is not UNSET:
            field_dict["message"] = message
        if shipment_id is not UNSET:
            field_dict["shipmentID"] = shipment_id
        if shipment_methods is not UNSET:
            field_dict["shipmentMethods"] = shipment_methods
        if dropoff_methods is not UNSET:
            field_dict["dropoffMethods"] = dropoff_methods
        if pickup_methods is not UNSET:
            field_dict["pickupMethods"] = pickup_methods
        if field_ is not UNSET:
            field_dict[""] = field_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.insert_shipment_response_200_dropoff_methods import InsertShipmentResponse200DropoffMethods
        from ..models.insert_shipment_response_200_pickup_methods import InsertShipmentResponse200PickupMethods
        from ..models.insert_shipment_response_200_shipment_methods import InsertShipmentResponse200ShipmentMethods

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        shipment_id = d.pop("shipmentID", UNSET)

        _shipment_methods = d.pop("shipmentMethods", UNSET)
        shipment_methods: InsertShipmentResponse200ShipmentMethods | Unset
        if isinstance(_shipment_methods, Unset):
            shipment_methods = UNSET
        else:
            shipment_methods = InsertShipmentResponse200ShipmentMethods.from_dict(_shipment_methods)

        _dropoff_methods = d.pop("dropoffMethods", UNSET)
        dropoff_methods: InsertShipmentResponse200DropoffMethods | Unset
        if isinstance(_dropoff_methods, Unset):
            dropoff_methods = UNSET
        else:
            dropoff_methods = InsertShipmentResponse200DropoffMethods.from_dict(_dropoff_methods)

        _pickup_methods = d.pop("pickupMethods", UNSET)
        pickup_methods: InsertShipmentResponse200PickupMethods | Unset
        if isinstance(_pickup_methods, Unset):
            pickup_methods = UNSET
        else:
            pickup_methods = InsertShipmentResponse200PickupMethods.from_dict(_pickup_methods)

        field_ = d.pop("", UNSET)

        insert_shipment_response_200 = cls(
            status=status,
            code=code,
            message=message,
            shipment_id=shipment_id,
            shipment_methods=shipment_methods,
            dropoff_methods=dropoff_methods,
            pickup_methods=pickup_methods,
            field_=field_,
        )

        insert_shipment_response_200.additional_properties = d
        return insert_shipment_response_200

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

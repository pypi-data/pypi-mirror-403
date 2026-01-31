from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.status import Status
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetStatusResponse200Shipment")


@_attrs_define
class GetStatusResponse200Shipment:
    """
    Attributes:
        shipment_id (int | Unset):
        created_at (str | Unset):
        order_number (str | Unset):
        reference (str | Unset):
        status (Status | Unset): Shipment status
    """

    shipment_id: int | Unset = UNSET
    created_at: str | Unset = UNSET
    order_number: str | Unset = UNSET
    reference: str | Unset = UNSET
    status: Status | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment_id = self.shipment_id

        created_at = self.created_at

        order_number = self.order_number

        reference = self.reference

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if shipment_id is not UNSET:
            field_dict["shipmentID"] = shipment_id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if order_number is not UNSET:
            field_dict["orderNumber"] = order_number
        if reference is not UNSET:
            field_dict["reference"] = reference
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        shipment_id = d.pop("shipmentID", UNSET)

        created_at = d.pop("createdAt", UNSET)

        order_number = d.pop("orderNumber", UNSET)

        reference = d.pop("reference", UNSET)

        _status = d.pop("status", UNSET)
        status: Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = Status(_status)

        get_status_response_200_shipment = cls(
            shipment_id=shipment_id,
            created_at=created_at,
            order_number=order_number,
            reference=reference,
            status=status,
        )

        get_status_response_200_shipment.additional_properties = d
        return get_status_response_200_shipment

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

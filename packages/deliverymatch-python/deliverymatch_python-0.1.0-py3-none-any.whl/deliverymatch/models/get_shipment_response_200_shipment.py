from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.status import Status
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetShipmentResponse200Shipment")


@_attrs_define
class GetShipmentResponse200Shipment:
    """
    Attributes:
        shipment_id (float | Unset):
        created_at (str | Unset):
        order_number (str | Unset):
        reference (str | Unset):
        language (str | Unset):
        currency (str | Unset):
        first_pickup_date (str | Unset):
        note (str | Unset):
        status (Status | Unset): Shipment status
        code (str | Unset):
    """

    shipment_id: float | Unset = UNSET
    created_at: str | Unset = UNSET
    order_number: str | Unset = UNSET
    reference: str | Unset = UNSET
    language: str | Unset = UNSET
    currency: str | Unset = UNSET
    first_pickup_date: str | Unset = UNSET
    note: str | Unset = UNSET
    status: Status | Unset = UNSET
    code: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        shipment_id = self.shipment_id

        created_at = self.created_at

        order_number = self.order_number

        reference = self.reference

        language = self.language

        currency = self.currency

        first_pickup_date = self.first_pickup_date

        note = self.note

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        code = self.code

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
        if language is not UNSET:
            field_dict["language"] = language
        if currency is not UNSET:
            field_dict["currency"] = currency
        if first_pickup_date is not UNSET:
            field_dict["firstPickupDate"] = first_pickup_date
        if note is not UNSET:
            field_dict["note"] = note
        if status is not UNSET:
            field_dict["status"] = status
        if code is not UNSET:
            field_dict["code"] = code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        shipment_id = d.pop("shipmentID", UNSET)

        created_at = d.pop("createdAt", UNSET)

        order_number = d.pop("orderNumber", UNSET)

        reference = d.pop("reference", UNSET)

        language = d.pop("language", UNSET)

        currency = d.pop("currency", UNSET)

        first_pickup_date = d.pop("firstPickupDate", UNSET)

        note = d.pop("note", UNSET)

        _status = d.pop("status", UNSET)
        status: Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = Status(_status)

        code = d.pop("code", UNSET)

        get_shipment_response_200_shipment = cls(
            shipment_id=shipment_id,
            created_at=created_at,
            order_number=order_number,
            reference=reference,
            language=language,
            currency=currency,
            first_pickup_date=first_pickup_date,
            note=note,
            status=status,
            code=code,
        )

        get_shipment_response_200_shipment.additional_properties = d
        return get_shipment_response_200_shipment

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

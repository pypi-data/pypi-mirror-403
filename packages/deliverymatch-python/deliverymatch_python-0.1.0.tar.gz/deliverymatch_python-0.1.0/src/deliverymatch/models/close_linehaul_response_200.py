from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CloseLinehaulResponse200")


@_attrs_define
class CloseLinehaulResponse200:
    """
    Attributes:
        status (str | Unset):
        code (int | Unset):
        message (str | Unset):
        shipment_id (int | Unset):
    """

    status: str | Unset = UNSET
    code: int | Unset = UNSET
    message: str | Unset = UNSET
    shipment_id: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        code = self.code

        message = self.message

        shipment_id = self.shipment_id

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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status", UNSET)

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        shipment_id = d.pop("shipmentID", UNSET)

        close_linehaul_response_200 = cls(
            status=status,
            code=code,
            message=message,
            shipment_id=shipment_id,
        )

        close_linehaul_response_200.additional_properties = d
        return close_linehaul_response_200

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

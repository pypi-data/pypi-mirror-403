from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_locations_response_200_dropoff_methods import GetLocationsResponse200DropoffMethods


T = TypeVar("T", bound="GetLocationsResponse200")


@_attrs_define
class GetLocationsResponse200:
    """
    Attributes:
        status (str | Unset):
        code (float | Unset):
        message (str | Unset):
        shipment_id (float | Unset):
        dropoff_methods (GetLocationsResponse200DropoffMethods | Unset):
    """

    status: str | Unset = UNSET
    code: float | Unset = UNSET
    message: str | Unset = UNSET
    shipment_id: float | Unset = UNSET
    dropoff_methods: GetLocationsResponse200DropoffMethods | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        code = self.code

        message = self.message

        shipment_id = self.shipment_id

        dropoff_methods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.dropoff_methods, Unset):
            dropoff_methods = self.dropoff_methods.to_dict()

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
        if dropoff_methods is not UNSET:
            field_dict["dropoffMethods"] = dropoff_methods

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_locations_response_200_dropoff_methods import GetLocationsResponse200DropoffMethods

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        shipment_id = d.pop("shipmentID", UNSET)

        _dropoff_methods = d.pop("dropoffMethods", UNSET)
        dropoff_methods: GetLocationsResponse200DropoffMethods | Unset
        if isinstance(_dropoff_methods, Unset):
            dropoff_methods = UNSET
        else:
            dropoff_methods = GetLocationsResponse200DropoffMethods.from_dict(_dropoff_methods)

        get_locations_response_200 = cls(
            status=status,
            code=code,
            message=message,
            shipment_id=shipment_id,
            dropoff_methods=dropoff_methods,
        )

        get_locations_response_200.additional_properties = d
        return get_locations_response_200

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

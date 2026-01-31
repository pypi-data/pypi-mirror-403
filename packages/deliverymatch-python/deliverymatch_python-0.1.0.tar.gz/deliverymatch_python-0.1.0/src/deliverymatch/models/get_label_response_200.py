from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_label_response_200_packages_item import GetLabelResponse200PackagesItem


T = TypeVar("T", bound="GetLabelResponse200")


@_attrs_define
class GetLabelResponse200:
    """
    Attributes:
        status (str | Unset):
        code (float | Unset):
        message (str | Unset):
        shipment_id (float | Unset):
        order_number (str | Unset):
        reference (str | Unset):
        label_url (str | Unset):
        zpl (str | Unset):
        packages (list[GetLabelResponse200PackagesItem] | Unset):
    """

    status: str | Unset = UNSET
    code: float | Unset = UNSET
    message: str | Unset = UNSET
    shipment_id: float | Unset = UNSET
    order_number: str | Unset = UNSET
    reference: str | Unset = UNSET
    label_url: str | Unset = UNSET
    zpl: str | Unset = UNSET
    packages: list[GetLabelResponse200PackagesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        code = self.code

        message = self.message

        shipment_id = self.shipment_id

        order_number = self.order_number

        reference = self.reference

        label_url = self.label_url

        zpl = self.zpl

        packages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.packages, Unset):
            packages = []
            for packages_item_data in self.packages:
                packages_item = packages_item_data.to_dict()
                packages.append(packages_item)

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
        if order_number is not UNSET:
            field_dict["orderNumber"] = order_number
        if reference is not UNSET:
            field_dict["reference"] = reference
        if label_url is not UNSET:
            field_dict["labelURL"] = label_url
        if zpl is not UNSET:
            field_dict["ZPL"] = zpl
        if packages is not UNSET:
            field_dict["packages"] = packages

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_label_response_200_packages_item import GetLabelResponse200PackagesItem

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        shipment_id = d.pop("shipmentID", UNSET)

        order_number = d.pop("orderNumber", UNSET)

        reference = d.pop("reference", UNSET)

        label_url = d.pop("labelURL", UNSET)

        zpl = d.pop("ZPL", UNSET)

        _packages = d.pop("packages", UNSET)
        packages: list[GetLabelResponse200PackagesItem] | Unset = UNSET
        if _packages is not UNSET:
            packages = []
            for packages_item_data in _packages:
                packages_item = GetLabelResponse200PackagesItem.from_dict(packages_item_data)

                packages.append(packages_item)

        get_label_response_200 = cls(
            status=status,
            code=code,
            message=message,
            shipment_id=shipment_id,
            order_number=order_number,
            reference=reference,
            label_url=label_url,
            zpl=zpl,
            packages=packages,
        )

        get_label_response_200.additional_properties = d
        return get_label_response_200

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

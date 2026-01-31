from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.address import Address
    from ..models.contact import Contact
    from ..models.customer_customs_info import CustomerCustomsInfo


T = TypeVar("T", bound="Customer")


@_attrs_define
class Customer:
    """Customer address, billing, contact and customs information

    Attributes:
        address (Address): General address information of a given individual
        id (int | Unset): Customer ID
        billing (Address | Unset): General address information of a given individual
        contact (Contact | Unset): General contact information of a given individual
        customs_info (CustomerCustomsInfo | Unset):
    """

    address: Address
    id: int | Unset = UNSET
    billing: Address | Unset = UNSET
    contact: Contact | Unset = UNSET
    customs_info: CustomerCustomsInfo | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address.to_dict()

        id = self.id

        billing: dict[str, Any] | Unset = UNSET
        if not isinstance(self.billing, Unset):
            billing = self.billing.to_dict()

        contact: dict[str, Any] | Unset = UNSET
        if not isinstance(self.contact, Unset):
            contact = self.contact.to_dict()

        customs_info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.customs_info, Unset):
            customs_info = self.customs_info.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if billing is not UNSET:
            field_dict["billing"] = billing
        if contact is not UNSET:
            field_dict["contact"] = contact
        if customs_info is not UNSET:
            field_dict["customsInfo"] = customs_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.address import Address
        from ..models.contact import Contact
        from ..models.customer_customs_info import CustomerCustomsInfo

        d = dict(src_dict)
        address = Address.from_dict(d.pop("address"))

        id = d.pop("id", UNSET)

        _billing = d.pop("billing", UNSET)
        billing: Address | Unset
        if isinstance(_billing, Unset):
            billing = UNSET
        else:
            billing = Address.from_dict(_billing)

        _contact = d.pop("contact", UNSET)
        contact: Contact | Unset
        if isinstance(_contact, Unset):
            contact = UNSET
        else:
            contact = Contact.from_dict(_contact)

        _customs_info = d.pop("customsInfo", UNSET)
        customs_info: CustomerCustomsInfo | Unset
        if isinstance(_customs_info, Unset):
            customs_info = UNSET
        else:
            customs_info = CustomerCustomsInfo.from_dict(_customs_info)

        customer = cls(
            address=address,
            id=id,
            billing=billing,
            contact=contact,
            customs_info=customs_info,
        )

        customer.additional_properties = d
        return customer

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

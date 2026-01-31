from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.address import Address
    from ..models.contact import Contact
    from ..models.sender_customs_info import SenderCustomsInfo


T = TypeVar("T", bound="Sender")


@_attrs_define
class Sender:
    """Sender address and contact information

    Attributes:
        address (Address): General address information of a given individual
        id (str | Unset): Sender ID
        contact (Contact | Unset): General contact information of a given individual
        customs_info (SenderCustomsInfo | Unset):
    """

    address: Address
    id: str | Unset = UNSET
    contact: Contact | Unset = UNSET
    customs_info: SenderCustomsInfo | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address.to_dict()

        id = self.id

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
        if contact is not UNSET:
            field_dict["contact"] = contact
        if customs_info is not UNSET:
            field_dict["customsInfo"] = customs_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.address import Address
        from ..models.contact import Contact
        from ..models.sender_customs_info import SenderCustomsInfo

        d = dict(src_dict)
        address = Address.from_dict(d.pop("address"))

        id = d.pop("id", UNSET)

        _contact = d.pop("contact", UNSET)
        contact: Contact | Unset
        if isinstance(_contact, Unset):
            contact = UNSET
        else:
            contact = Contact.from_dict(_contact)

        _customs_info = d.pop("customsInfo", UNSET)
        customs_info: SenderCustomsInfo | Unset
        if isinstance(_customs_info, Unset):
            customs_info = UNSET
        else:
            customs_info = SenderCustomsInfo.from_dict(_customs_info)

        sender = cls(
            address=address,
            id=id,
            contact=contact,
            customs_info=customs_info,
        )

        sender.additional_properties = d
        return sender

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

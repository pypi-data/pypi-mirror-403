from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomerCustomsInfo")


@_attrs_define
class CustomerCustomsInfo:
    """
    Attributes:
        eori_number (str | Unset):  Example: GB092999935000.
        vat_number (str | Unset):  Example: GB439161685.
        exworks_account (str | Unset):
    """

    eori_number: str | Unset = UNSET
    vat_number: str | Unset = UNSET
    exworks_account: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eori_number = self.eori_number

        vat_number = self.vat_number

        exworks_account = self.exworks_account

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if eori_number is not UNSET:
            field_dict["eori_number"] = eori_number
        if vat_number is not UNSET:
            field_dict["vat_number"] = vat_number
        if exworks_account is not UNSET:
            field_dict["exworks_account"] = exworks_account

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        eori_number = d.pop("eori_number", UNSET)

        vat_number = d.pop("vat_number", UNSET)

        exworks_account = d.pop("exworks_account", UNSET)

        customer_customs_info = cls(
            eori_number=eori_number,
            vat_number=vat_number,
            exworks_account=exworks_account,
        )

        customer_customs_info.additional_properties = d
        return customer_customs_info

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

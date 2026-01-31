from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLabelResponse200PackagesItem")


@_attrs_define
class GetLabelResponse200PackagesItem:
    """
    Attributes:
        barcode (str | Unset):
        zpl (str | Unset):
        label_url (str | Unset):
    """

    barcode: str | Unset = UNSET
    zpl: str | Unset = UNSET
    label_url: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        barcode = self.barcode

        zpl = self.zpl

        label_url = self.label_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if barcode is not UNSET:
            field_dict["barcode"] = barcode
        if zpl is not UNSET:
            field_dict["ZPL"] = zpl
        if label_url is not UNSET:
            field_dict["labelURL"] = label_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        barcode = d.pop("barcode", UNSET)

        zpl = d.pop("ZPL", UNSET)

        label_url = d.pop("labelURL", UNSET)

        get_label_response_200_packages_item = cls(
            barcode=barcode,
            zpl=zpl,
            label_url=label_url,
        )

        get_label_response_200_packages_item.additional_properties = d
        return get_label_response_200_packages_item

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

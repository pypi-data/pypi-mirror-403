from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Label")


@_attrs_define
class Label:
    """General information about the labels and tracking options

    Attributes:
        barcode (str | Unset): Label barcode/tracking number Example: 3S1234567891.
        tracking_url (str | Unset): Tracking URL Example: https://www.deliverymatch.nl/track/3S1234567891.
        pdf (str | Unset): A base64 encoded raw PDF label Example: SGFsbG8hIFdhcyBoZXQgZGUgbW9laXRlIHdhYXJkPyA7KQ==.
        zpl (str | Unset): A base64 encoded raw ZPL label Example: SGFsbG8hIFdhcyBoZXQgZGUgbW9laXRlIHdhYXJkPyA7KQ==.
    """

    barcode: str | Unset = UNSET
    tracking_url: str | Unset = UNSET
    pdf: str | Unset = UNSET
    zpl: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        barcode = self.barcode

        tracking_url = self.tracking_url

        pdf = self.pdf

        zpl = self.zpl

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if barcode is not UNSET:
            field_dict["barcode"] = barcode
        if tracking_url is not UNSET:
            field_dict["trackingURL"] = tracking_url
        if pdf is not UNSET:
            field_dict["PDF"] = pdf
        if zpl is not UNSET:
            field_dict["ZPL"] = zpl

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        barcode = d.pop("barcode", UNSET)

        tracking_url = d.pop("trackingURL", UNSET)

        pdf = d.pop("PDF", UNSET)

        zpl = d.pop("ZPL", UNSET)

        label = cls(
            barcode=barcode,
            tracking_url=tracking_url,
            pdf=pdf,
            zpl=zpl,
        )

        label.additional_properties = d
        return label

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

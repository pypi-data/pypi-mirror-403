from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetDesignResponse200DesignColors")


@_attrs_define
class GetDesignResponse200DesignColors:
    """
    Attributes:
        background (str | Unset):
        text (str | Unset):
        button_background (str | Unset):
        button_text (str | Unset):
        price_background (str | Unset):
        price_text (str | Unset):
        info_background (str | Unset):
        info_text (str | Unset):
        table_header (str | Unset):
        table_text (str | Unset):
        table_border (str | Unset):
        border (str | Unset):
    """

    background: str | Unset = UNSET
    text: str | Unset = UNSET
    button_background: str | Unset = UNSET
    button_text: str | Unset = UNSET
    price_background: str | Unset = UNSET
    price_text: str | Unset = UNSET
    info_background: str | Unset = UNSET
    info_text: str | Unset = UNSET
    table_header: str | Unset = UNSET
    table_text: str | Unset = UNSET
    table_border: str | Unset = UNSET
    border: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        background = self.background

        text = self.text

        button_background = self.button_background

        button_text = self.button_text

        price_background = self.price_background

        price_text = self.price_text

        info_background = self.info_background

        info_text = self.info_text

        table_header = self.table_header

        table_text = self.table_text

        table_border = self.table_border

        border = self.border

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if background is not UNSET:
            field_dict["background"] = background
        if text is not UNSET:
            field_dict["text"] = text
        if button_background is not UNSET:
            field_dict["button_background"] = button_background
        if button_text is not UNSET:
            field_dict["button_text"] = button_text
        if price_background is not UNSET:
            field_dict["price_background"] = price_background
        if price_text is not UNSET:
            field_dict["price_text"] = price_text
        if info_background is not UNSET:
            field_dict["info_background"] = info_background
        if info_text is not UNSET:
            field_dict["info_text"] = info_text
        if table_header is not UNSET:
            field_dict["table_header"] = table_header
        if table_text is not UNSET:
            field_dict["table_text"] = table_text
        if table_border is not UNSET:
            field_dict["table_border"] = table_border
        if border is not UNSET:
            field_dict["border"] = border

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        background = d.pop("background", UNSET)

        text = d.pop("text", UNSET)

        button_background = d.pop("button_background", UNSET)

        button_text = d.pop("button_text", UNSET)

        price_background = d.pop("price_background", UNSET)

        price_text = d.pop("price_text", UNSET)

        info_background = d.pop("info_background", UNSET)

        info_text = d.pop("info_text", UNSET)

        table_header = d.pop("table_header", UNSET)

        table_text = d.pop("table_text", UNSET)

        table_border = d.pop("table_border", UNSET)

        border = d.pop("border", UNSET)

        get_design_response_200_design_colors = cls(
            background=background,
            text=text,
            button_background=button_background,
            button_text=button_text,
            price_background=price_background,
            price_text=price_text,
            info_background=info_background,
            info_text=info_text,
            table_header=table_header,
            table_text=table_text,
            table_border=table_border,
            border=border,
        )

        get_design_response_200_design_colors.additional_properties = d
        return get_design_response_200_design_colors

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

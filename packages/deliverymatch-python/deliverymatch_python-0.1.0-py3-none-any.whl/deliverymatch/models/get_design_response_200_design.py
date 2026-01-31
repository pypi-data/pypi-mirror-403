from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_design_response_200_design_active import GetDesignResponse200DesignActive
    from ..models.get_design_response_200_design_carrier_logos import GetDesignResponse200DesignCarrierLogos
    from ..models.get_design_response_200_design_colors import GetDesignResponse200DesignColors
    from ..models.get_design_response_200_design_num_options import GetDesignResponse200DesignNumOptions
    from ..models.get_design_response_200_design_text import GetDesignResponse200DesignText


T = TypeVar("T", bound="GetDesignResponse200Design")


@_attrs_define
class GetDesignResponse200Design:
    """
    Attributes:
        colors (GetDesignResponse200DesignColors | Unset):
        active (GetDesignResponse200DesignActive | Unset):
        text (GetDesignResponse200DesignText | Unset):
        num_options (GetDesignResponse200DesignNumOptions | Unset):
        show_carrier (bool | Unset):
        font (str | Unset):
        carrier_order (str | Unset):
        carrier_logos (GetDesignResponse200DesignCarrierLogos | Unset):
    """

    colors: GetDesignResponse200DesignColors | Unset = UNSET
    active: GetDesignResponse200DesignActive | Unset = UNSET
    text: GetDesignResponse200DesignText | Unset = UNSET
    num_options: GetDesignResponse200DesignNumOptions | Unset = UNSET
    show_carrier: bool | Unset = UNSET
    font: str | Unset = UNSET
    carrier_order: str | Unset = UNSET
    carrier_logos: GetDesignResponse200DesignCarrierLogos | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        colors: dict[str, Any] | Unset = UNSET
        if not isinstance(self.colors, Unset):
            colors = self.colors.to_dict()

        active: dict[str, Any] | Unset = UNSET
        if not isinstance(self.active, Unset):
            active = self.active.to_dict()

        text: dict[str, Any] | Unset = UNSET
        if not isinstance(self.text, Unset):
            text = self.text.to_dict()

        num_options: dict[str, Any] | Unset = UNSET
        if not isinstance(self.num_options, Unset):
            num_options = self.num_options.to_dict()

        show_carrier = self.show_carrier

        font = self.font

        carrier_order = self.carrier_order

        carrier_logos: dict[str, Any] | Unset = UNSET
        if not isinstance(self.carrier_logos, Unset):
            carrier_logos = self.carrier_logos.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if colors is not UNSET:
            field_dict["colors"] = colors
        if active is not UNSET:
            field_dict["active"] = active
        if text is not UNSET:
            field_dict["text"] = text
        if num_options is not UNSET:
            field_dict["num_options"] = num_options
        if show_carrier is not UNSET:
            field_dict["show_carrier"] = show_carrier
        if font is not UNSET:
            field_dict["font"] = font
        if carrier_order is not UNSET:
            field_dict["carrier_order"] = carrier_order
        if carrier_logos is not UNSET:
            field_dict["carrier_logos"] = carrier_logos

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_design_response_200_design_active import GetDesignResponse200DesignActive
        from ..models.get_design_response_200_design_carrier_logos import GetDesignResponse200DesignCarrierLogos
        from ..models.get_design_response_200_design_colors import GetDesignResponse200DesignColors
        from ..models.get_design_response_200_design_num_options import GetDesignResponse200DesignNumOptions
        from ..models.get_design_response_200_design_text import GetDesignResponse200DesignText

        d = dict(src_dict)
        _colors = d.pop("colors", UNSET)
        colors: GetDesignResponse200DesignColors | Unset
        if isinstance(_colors, Unset):
            colors = UNSET
        else:
            colors = GetDesignResponse200DesignColors.from_dict(_colors)

        _active = d.pop("active", UNSET)
        active: GetDesignResponse200DesignActive | Unset
        if isinstance(_active, Unset):
            active = UNSET
        else:
            active = GetDesignResponse200DesignActive.from_dict(_active)

        _text = d.pop("text", UNSET)
        text: GetDesignResponse200DesignText | Unset
        if isinstance(_text, Unset):
            text = UNSET
        else:
            text = GetDesignResponse200DesignText.from_dict(_text)

        _num_options = d.pop("num_options", UNSET)
        num_options: GetDesignResponse200DesignNumOptions | Unset
        if isinstance(_num_options, Unset):
            num_options = UNSET
        else:
            num_options = GetDesignResponse200DesignNumOptions.from_dict(_num_options)

        show_carrier = d.pop("show_carrier", UNSET)

        font = d.pop("font", UNSET)

        carrier_order = d.pop("carrier_order", UNSET)

        _carrier_logos = d.pop("carrier_logos", UNSET)
        carrier_logos: GetDesignResponse200DesignCarrierLogos | Unset
        if isinstance(_carrier_logos, Unset):
            carrier_logos = UNSET
        else:
            carrier_logos = GetDesignResponse200DesignCarrierLogos.from_dict(_carrier_logos)

        get_design_response_200_design = cls(
            colors=colors,
            active=active,
            text=text,
            num_options=num_options,
            show_carrier=show_carrier,
            font=font,
            carrier_order=carrier_order,
            carrier_logos=carrier_logos,
        )

        get_design_response_200_design.additional_properties = d
        return get_design_response_200_design

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetDesignResponse200DesignText")


@_attrs_define
class GetDesignResponse200DesignText:
    """
    Attributes:
        delivery_time_title (str | Unset):
        delivery_time_description (str | Unset):
        delivery_unknown_title (str | Unset):
        delivery_unknown_description (str | Unset):
        category_title (str | Unset):
        category_description (str | Unset):
        text_popup (str | Unset):
        text_confirm (str | Unset):
        dropoff_title (str | Unset):
        dropoff_description (str | Unset):
        category_title_dropoff (str | Unset):
        category_description_dropoff (str | Unset):
        text_popup_dropoff (str | Unset):
        text_confirm_dropoff (str | Unset):
        pickup_title (str | Unset):
        pickup_description (str | Unset):
        category_title_pickup (str | Unset):
        category_description_pickup (str | Unset):
        text_popup_pickup (str | Unset):
        text_confirm_pickup (str | Unset):
    """

    delivery_time_title: str | Unset = UNSET
    delivery_time_description: str | Unset = UNSET
    delivery_unknown_title: str | Unset = UNSET
    delivery_unknown_description: str | Unset = UNSET
    category_title: str | Unset = UNSET
    category_description: str | Unset = UNSET
    text_popup: str | Unset = UNSET
    text_confirm: str | Unset = UNSET
    dropoff_title: str | Unset = UNSET
    dropoff_description: str | Unset = UNSET
    category_title_dropoff: str | Unset = UNSET
    category_description_dropoff: str | Unset = UNSET
    text_popup_dropoff: str | Unset = UNSET
    text_confirm_dropoff: str | Unset = UNSET
    pickup_title: str | Unset = UNSET
    pickup_description: str | Unset = UNSET
    category_title_pickup: str | Unset = UNSET
    category_description_pickup: str | Unset = UNSET
    text_popup_pickup: str | Unset = UNSET
    text_confirm_pickup: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        delivery_time_title = self.delivery_time_title

        delivery_time_description = self.delivery_time_description

        delivery_unknown_title = self.delivery_unknown_title

        delivery_unknown_description = self.delivery_unknown_description

        category_title = self.category_title

        category_description = self.category_description

        text_popup = self.text_popup

        text_confirm = self.text_confirm

        dropoff_title = self.dropoff_title

        dropoff_description = self.dropoff_description

        category_title_dropoff = self.category_title_dropoff

        category_description_dropoff = self.category_description_dropoff

        text_popup_dropoff = self.text_popup_dropoff

        text_confirm_dropoff = self.text_confirm_dropoff

        pickup_title = self.pickup_title

        pickup_description = self.pickup_description

        category_title_pickup = self.category_title_pickup

        category_description_pickup = self.category_description_pickup

        text_popup_pickup = self.text_popup_pickup

        text_confirm_pickup = self.text_confirm_pickup

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if delivery_time_title is not UNSET:
            field_dict["delivery_time_title"] = delivery_time_title
        if delivery_time_description is not UNSET:
            field_dict["delivery_time_description"] = delivery_time_description
        if delivery_unknown_title is not UNSET:
            field_dict["delivery_unknown_title"] = delivery_unknown_title
        if delivery_unknown_description is not UNSET:
            field_dict["delivery_unknown_description"] = delivery_unknown_description
        if category_title is not UNSET:
            field_dict["category_title"] = category_title
        if category_description is not UNSET:
            field_dict["category_description"] = category_description
        if text_popup is not UNSET:
            field_dict["text_popup"] = text_popup
        if text_confirm is not UNSET:
            field_dict["text_confirm"] = text_confirm
        if dropoff_title is not UNSET:
            field_dict["dropoff_title"] = dropoff_title
        if dropoff_description is not UNSET:
            field_dict["dropoff_description"] = dropoff_description
        if category_title_dropoff is not UNSET:
            field_dict["category_title_dropoff"] = category_title_dropoff
        if category_description_dropoff is not UNSET:
            field_dict["category_description_dropoff"] = category_description_dropoff
        if text_popup_dropoff is not UNSET:
            field_dict["text_popup_dropoff"] = text_popup_dropoff
        if text_confirm_dropoff is not UNSET:
            field_dict["text_confirm_dropoff"] = text_confirm_dropoff
        if pickup_title is not UNSET:
            field_dict["pickup_title"] = pickup_title
        if pickup_description is not UNSET:
            field_dict["pickup_description"] = pickup_description
        if category_title_pickup is not UNSET:
            field_dict["category_title_pickup"] = category_title_pickup
        if category_description_pickup is not UNSET:
            field_dict["category_description_pickup"] = category_description_pickup
        if text_popup_pickup is not UNSET:
            field_dict["text_popup_pickup"] = text_popup_pickup
        if text_confirm_pickup is not UNSET:
            field_dict["text_confirm_pickup"] = text_confirm_pickup

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        delivery_time_title = d.pop("delivery_time_title", UNSET)

        delivery_time_description = d.pop("delivery_time_description", UNSET)

        delivery_unknown_title = d.pop("delivery_unknown_title", UNSET)

        delivery_unknown_description = d.pop("delivery_unknown_description", UNSET)

        category_title = d.pop("category_title", UNSET)

        category_description = d.pop("category_description", UNSET)

        text_popup = d.pop("text_popup", UNSET)

        text_confirm = d.pop("text_confirm", UNSET)

        dropoff_title = d.pop("dropoff_title", UNSET)

        dropoff_description = d.pop("dropoff_description", UNSET)

        category_title_dropoff = d.pop("category_title_dropoff", UNSET)

        category_description_dropoff = d.pop("category_description_dropoff", UNSET)

        text_popup_dropoff = d.pop("text_popup_dropoff", UNSET)

        text_confirm_dropoff = d.pop("text_confirm_dropoff", UNSET)

        pickup_title = d.pop("pickup_title", UNSET)

        pickup_description = d.pop("pickup_description", UNSET)

        category_title_pickup = d.pop("category_title_pickup", UNSET)

        category_description_pickup = d.pop("category_description_pickup", UNSET)

        text_popup_pickup = d.pop("text_popup_pickup", UNSET)

        text_confirm_pickup = d.pop("text_confirm_pickup", UNSET)

        get_design_response_200_design_text = cls(
            delivery_time_title=delivery_time_title,
            delivery_time_description=delivery_time_description,
            delivery_unknown_title=delivery_unknown_title,
            delivery_unknown_description=delivery_unknown_description,
            category_title=category_title,
            category_description=category_description,
            text_popup=text_popup,
            text_confirm=text_confirm,
            dropoff_title=dropoff_title,
            dropoff_description=dropoff_description,
            category_title_dropoff=category_title_dropoff,
            category_description_dropoff=category_description_dropoff,
            text_popup_dropoff=text_popup_dropoff,
            text_confirm_dropoff=text_confirm_dropoff,
            pickup_title=pickup_title,
            pickup_description=pickup_description,
            category_title_pickup=category_title_pickup,
            category_description_pickup=category_description_pickup,
            text_popup_pickup=text_popup_pickup,
            text_confirm_pickup=text_confirm_pickup,
        )

        get_design_response_200_design_text.additional_properties = d
        return get_design_response_200_design_text

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetServicesBody")


@_attrs_define
class GetServicesBody:
    """
    Attributes:
        country_from (str | Unset): Country of origin Example: NL.
        country_to (str | Unset): Destination country Example: BE.
    """

    country_from: str | Unset = UNSET
    country_to: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        country_from = self.country_from

        country_to = self.country_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if country_from is not UNSET:
            field_dict["countryFrom"] = country_from
        if country_to is not UNSET:
            field_dict["countryTo"] = country_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        country_from = d.pop("countryFrom", UNSET)

        country_to = d.pop("countryTo", UNSET)

        get_services_body = cls(
            country_from=country_from,
            country_to=country_to,
        )

        get_services_body.additional_properties = d
        return get_services_body

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

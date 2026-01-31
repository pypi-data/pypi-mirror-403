from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem,
    )


T = TypeVar("T", bound="GetLocationsResponse200DropoffMethodsAll")


@_attrs_define
class GetLocationsResponse200DropoffMethodsAll:
    """
    Attributes:
        yyyy_mm_dd (list[GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem] | Unset):
    """

    yyyy_mm_dd: list[GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        yyyy_mm_dd: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.yyyy_mm_dd, Unset):
            yyyy_mm_dd = []
            for yyyy_mm_dd_item_data in self.yyyy_mm_dd:
                yyyy_mm_dd_item = yyyy_mm_dd_item_data.to_dict()
                yyyy_mm_dd.append(yyyy_mm_dd_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if yyyy_mm_dd is not UNSET:
            field_dict["YYYY-MM-DD"] = yyyy_mm_dd

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem,
        )

        d = dict(src_dict)
        _yyyy_mm_dd = d.pop("YYYY-MM-DD", UNSET)
        yyyy_mm_dd: list[GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem] | Unset = UNSET
        if _yyyy_mm_dd is not UNSET:
            yyyy_mm_dd = []
            for yyyy_mm_dd_item_data in _yyyy_mm_dd:
                yyyy_mm_dd_item = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItem.from_dict(yyyy_mm_dd_item_data)

                yyyy_mm_dd.append(yyyy_mm_dd_item)

        get_locations_response_200_dropoff_methods_all = cls(
            yyyy_mm_dd=yyyy_mm_dd,
        )

        get_locations_response_200_dropoff_methods_all.additional_properties = d
        return get_locations_response_200_dropoff_methods_all

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

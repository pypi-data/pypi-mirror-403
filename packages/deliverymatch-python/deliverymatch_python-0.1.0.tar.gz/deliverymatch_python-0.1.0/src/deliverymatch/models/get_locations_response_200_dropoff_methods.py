from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_locations_response_200_dropoff_methods_all import GetLocationsResponse200DropoffMethodsAll


T = TypeVar("T", bound="GetLocationsResponse200DropoffMethods")


@_attrs_define
class GetLocationsResponse200DropoffMethods:
    """
    Attributes:
        all_ (GetLocationsResponse200DropoffMethodsAll | Unset):
    """

    all_: GetLocationsResponse200DropoffMethodsAll | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        all_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.all_, Unset):
            all_ = self.all_.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if all_ is not UNSET:
            field_dict["all"] = all_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_locations_response_200_dropoff_methods_all import GetLocationsResponse200DropoffMethodsAll

        d = dict(src_dict)
        _all_ = d.pop("all", UNSET)
        all_: GetLocationsResponse200DropoffMethodsAll | Unset
        if isinstance(_all_, Unset):
            all_ = UNSET
        else:
            all_ = GetLocationsResponse200DropoffMethodsAll.from_dict(_all_)

        get_locations_response_200_dropoff_methods = cls(
            all_=all_,
        )

        get_locations_response_200_dropoff_methods.additional_properties = d
        return get_locations_response_200_dropoff_methods

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

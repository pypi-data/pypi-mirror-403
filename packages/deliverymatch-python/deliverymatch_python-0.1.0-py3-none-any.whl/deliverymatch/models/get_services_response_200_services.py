from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_services_response_200_services_services_item import GetServicesResponse200ServicesServicesItem


T = TypeVar("T", bound="GetServicesResponse200Services")


@_attrs_define
class GetServicesResponse200Services:
    """
    Attributes:
        services (list[GetServicesResponse200ServicesServicesItem] | Unset):
    """

    services: list[GetServicesResponse200ServicesServicesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        services: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.services, Unset):
            services = []
            for services_item_data in self.services:
                services_item = services_item_data.to_dict()
                services.append(services_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if services is not UNSET:
            field_dict["services"] = services

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_services_response_200_services_services_item import GetServicesResponse200ServicesServicesItem

        d = dict(src_dict)
        _services = d.pop("services", UNSET)
        services: list[GetServicesResponse200ServicesServicesItem] | Unset = UNSET
        if _services is not UNSET:
            services = []
            for services_item_data in _services:
                services_item = GetServicesResponse200ServicesServicesItem.from_dict(services_item_data)

                services.append(services_item)

        get_services_response_200_services = cls(
            services=services,
        )

        get_services_response_200_services.additional_properties = d
        return get_services_response_200_services

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

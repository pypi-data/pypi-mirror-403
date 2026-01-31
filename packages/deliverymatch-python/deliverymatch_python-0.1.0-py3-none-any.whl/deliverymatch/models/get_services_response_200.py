from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_services_response_200_services import GetServicesResponse200Services


T = TypeVar("T", bound="GetServicesResponse200")


@_attrs_define
class GetServicesResponse200:
    """
    Attributes:
        services (GetServicesResponse200Services | Unset):
    """

    services: GetServicesResponse200Services | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        services: dict[str, Any] | Unset = UNSET
        if not isinstance(self.services, Unset):
            services = self.services.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if services is not UNSET:
            field_dict["services"] = services

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_services_response_200_services import GetServicesResponse200Services

        d = dict(src_dict)
        _services = d.pop("services", UNSET)
        services: GetServicesResponse200Services | Unset
        if isinstance(_services, Unset):
            services = UNSET
        else:
            services = GetServicesResponse200Services.from_dict(_services)

        get_services_response_200 = cls(
            services=services,
        )

        get_services_response_200.additional_properties = d
        return get_services_response_200

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

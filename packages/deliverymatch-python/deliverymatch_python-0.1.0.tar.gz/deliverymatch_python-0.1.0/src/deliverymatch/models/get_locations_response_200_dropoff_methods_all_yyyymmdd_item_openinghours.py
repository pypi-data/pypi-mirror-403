from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_1 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours1,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_2 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours2,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_3 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours3,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_4 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours4,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_5 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours5,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_6 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours6,
    )
    from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_7 import (
        GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours7,
    )


T = TypeVar("T", bound="GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours")


@_attrs_define
class GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours:
    """
    Attributes:
        field_1 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours1 | Unset):
        field_2 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours2 | Unset):
        field_3 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours3 | Unset):
        field_4 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours4 | Unset):
        field_5 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours5 | Unset):
        field_6 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours6 | Unset):
        field_7 (GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours7 | Unset):
    """

    field_1: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours1 | Unset = UNSET
    field_2: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours2 | Unset = UNSET
    field_3: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours3 | Unset = UNSET
    field_4: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours4 | Unset = UNSET
    field_5: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours5 | Unset = UNSET
    field_6: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours6 | Unset = UNSET
    field_7: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours7 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_1: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_1, Unset):
            field_1 = self.field_1.to_dict()

        field_2: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_2, Unset):
            field_2 = self.field_2.to_dict()

        field_3: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_3, Unset):
            field_3 = self.field_3.to_dict()

        field_4: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_4, Unset):
            field_4 = self.field_4.to_dict()

        field_5: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_5, Unset):
            field_5 = self.field_5.to_dict()

        field_6: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_6, Unset):
            field_6 = self.field_6.to_dict()

        field_7: dict[str, Any] | Unset = UNSET
        if not isinstance(self.field_7, Unset):
            field_7 = self.field_7.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field_1 is not UNSET:
            field_dict["1"] = field_1
        if field_2 is not UNSET:
            field_dict["2"] = field_2
        if field_3 is not UNSET:
            field_dict["3"] = field_3
        if field_4 is not UNSET:
            field_dict["4"] = field_4
        if field_5 is not UNSET:
            field_dict["5"] = field_5
        if field_6 is not UNSET:
            field_dict["6"] = field_6
        if field_7 is not UNSET:
            field_dict["7"] = field_7

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_1 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours1,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_2 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours2,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_3 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours3,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_4 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours4,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_5 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours5,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_6 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours6,
        )
        from ..models.get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours_7 import (
            GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours7,
        )

        d = dict(src_dict)
        _field_1 = d.pop("1", UNSET)
        field_1: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours1 | Unset
        if isinstance(_field_1, Unset):
            field_1 = UNSET
        else:
            field_1 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours1.from_dict(_field_1)

        _field_2 = d.pop("2", UNSET)
        field_2: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours2 | Unset
        if isinstance(_field_2, Unset):
            field_2 = UNSET
        else:
            field_2 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours2.from_dict(_field_2)

        _field_3 = d.pop("3", UNSET)
        field_3: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours3 | Unset
        if isinstance(_field_3, Unset):
            field_3 = UNSET
        else:
            field_3 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours3.from_dict(_field_3)

        _field_4 = d.pop("4", UNSET)
        field_4: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours4 | Unset
        if isinstance(_field_4, Unset):
            field_4 = UNSET
        else:
            field_4 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours4.from_dict(_field_4)

        _field_5 = d.pop("5", UNSET)
        field_5: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours5 | Unset
        if isinstance(_field_5, Unset):
            field_5 = UNSET
        else:
            field_5 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours5.from_dict(_field_5)

        _field_6 = d.pop("6", UNSET)
        field_6: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours6 | Unset
        if isinstance(_field_6, Unset):
            field_6 = UNSET
        else:
            field_6 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours6.from_dict(_field_6)

        _field_7 = d.pop("7", UNSET)
        field_7: GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours7 | Unset
        if isinstance(_field_7, Unset):
            field_7 = UNSET
        else:
            field_7 = GetLocationsResponse200DropoffMethodsAllYYYYMMDDItemOpeninghours7.from_dict(_field_7)

        get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours = cls(
            field_1=field_1,
            field_2=field_2,
            field_3=field_3,
            field_4=field_4,
            field_5=field_5,
            field_6=field_6,
            field_7=field_7,
        )

        get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours.additional_properties = d
        return get_locations_response_200_dropoff_methods_all_yyyymmdd_item_openinghours

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

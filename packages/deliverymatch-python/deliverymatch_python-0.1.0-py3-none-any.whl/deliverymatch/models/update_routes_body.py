from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_routes_body_adjustment import UpdateRoutesBodyAdjustment
    from ..models.update_routes_body_filter import UpdateRoutesBodyFilter


T = TypeVar("T", bound="UpdateRoutesBody")


@_attrs_define
class UpdateRoutesBody:
    """
    Attributes:
        filter_ (UpdateRoutesBodyFilter): The filters to apply
        adjustment (UpdateRoutesBodyAdjustment): Atleast one adjustment field is required
        test (bool | Unset): **True**: adjustment not saved, only returns amount of routes that would be updated

            **False**: adjustments will be saved and routes will be updated.
    """

    filter_: UpdateRoutesBodyFilter
    adjustment: UpdateRoutesBodyAdjustment
    test: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        filter_ = self.filter_.to_dict()

        adjustment = self.adjustment.to_dict()

        test = self.test

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "filter": filter_,
                "adjustment": adjustment,
            }
        )
        if test is not UNSET:
            field_dict["test"] = test

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_routes_body_adjustment import UpdateRoutesBodyAdjustment
        from ..models.update_routes_body_filter import UpdateRoutesBodyFilter

        d = dict(src_dict)
        filter_ = UpdateRoutesBodyFilter.from_dict(d.pop("filter"))

        adjustment = UpdateRoutesBodyAdjustment.from_dict(d.pop("adjustment"))

        test = d.pop("test", UNSET)

        update_routes_body = cls(
            filter_=filter_,
            adjustment=adjustment,
            test=test,
        )

        update_routes_body.additional_properties = d
        return update_routes_body

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

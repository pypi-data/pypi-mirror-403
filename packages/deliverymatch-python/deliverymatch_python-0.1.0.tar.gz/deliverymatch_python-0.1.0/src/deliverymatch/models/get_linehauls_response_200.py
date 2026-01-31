from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_linehauls_response_200_linehauls_item import GetLinehaulsResponse200LinehaulsItem


T = TypeVar("T", bound="GetLinehaulsResponse200")


@_attrs_define
class GetLinehaulsResponse200:
    """
    Attributes:
        status (str | Unset):
        code (int | Unset):
        message (str | Unset):
        linehauls (list[GetLinehaulsResponse200LinehaulsItem] | Unset):
    """

    status: str | Unset = UNSET
    code: int | Unset = UNSET
    message: str | Unset = UNSET
    linehauls: list[GetLinehaulsResponse200LinehaulsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        code = self.code

        message = self.message

        linehauls: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.linehauls, Unset):
            linehauls = []
            for linehauls_item_data in self.linehauls:
                linehauls_item = linehauls_item_data.to_dict()
                linehauls.append(linehauls_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if code is not UNSET:
            field_dict["code"] = code
        if message is not UNSET:
            field_dict["message"] = message
        if linehauls is not UNSET:
            field_dict["linehauls"] = linehauls

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_linehauls_response_200_linehauls_item import GetLinehaulsResponse200LinehaulsItem

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        _linehauls = d.pop("linehauls", UNSET)
        linehauls: list[GetLinehaulsResponse200LinehaulsItem] | Unset = UNSET
        if _linehauls is not UNSET:
            linehauls = []
            for linehauls_item_data in _linehauls:
                linehauls_item = GetLinehaulsResponse200LinehaulsItem.from_dict(linehauls_item_data)

                linehauls.append(linehauls_item)

        get_linehauls_response_200 = cls(
            status=status,
            code=code,
            message=message,
            linehauls=linehauls,
        )

        get_linehauls_response_200.additional_properties = d
        return get_linehauls_response_200

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

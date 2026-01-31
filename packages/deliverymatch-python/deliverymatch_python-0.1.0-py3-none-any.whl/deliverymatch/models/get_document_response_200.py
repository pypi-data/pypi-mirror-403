from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetDocumentResponse200")


@_attrs_define
class GetDocumentResponse200:
    """
    Attributes:
        id (int | Unset):
        data (str | Unset):
        document_type (str | Unset):
        file_type (str | Unset):
    """

    id: int | Unset = UNSET
    data: str | Unset = UNSET
    document_type: str | Unset = UNSET
    file_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        data = self.data

        document_type = self.document_type

        file_type = self.file_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if data is not UNSET:
            field_dict["data"] = data
        if document_type is not UNSET:
            field_dict["documentType"] = document_type
        if file_type is not UNSET:
            field_dict["fileType"] = file_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        data = d.pop("data", UNSET)

        document_type = d.pop("documentType", UNSET)

        file_type = d.pop("fileType", UNSET)

        get_document_response_200 = cls(
            id=id,
            data=data,
            document_type=document_type,
            file_type=file_type,
        )

        get_document_response_200.additional_properties = d
        return get_document_response_200

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

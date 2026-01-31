from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.add_document_response_201_document_type import AddDocumentResponse201DocumentType
from ..models.add_document_response_201_file_type import AddDocumentResponse201FileType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AddDocumentResponse201")


@_attrs_define
class AddDocumentResponse201:
    """
    Attributes:
        id (int | Unset):
        document_type (AddDocumentResponse201DocumentType | Unset):
        file_type (AddDocumentResponse201FileType | Unset):
    """

    id: int | Unset = UNSET
    document_type: AddDocumentResponse201DocumentType | Unset = UNSET
    file_type: AddDocumentResponse201FileType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        document_type: str | Unset = UNSET
        if not isinstance(self.document_type, Unset):
            document_type = self.document_type.value

        file_type: str | Unset = UNSET
        if not isinstance(self.file_type, Unset):
            file_type = self.file_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if document_type is not UNSET:
            field_dict["documentType"] = document_type
        if file_type is not UNSET:
            field_dict["fileType"] = file_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _document_type = d.pop("documentType", UNSET)
        document_type: AddDocumentResponse201DocumentType | Unset
        if isinstance(_document_type, Unset):
            document_type = UNSET
        else:
            document_type = AddDocumentResponse201DocumentType(_document_type)

        _file_type = d.pop("fileType", UNSET)
        file_type: AddDocumentResponse201FileType | Unset
        if isinstance(_file_type, Unset):
            file_type = UNSET
        else:
            file_type = AddDocumentResponse201FileType(_file_type)

        add_document_response_201 = cls(
            id=id,
            document_type=document_type,
            file_type=file_type,
        )

        add_document_response_201.additional_properties = d
        return add_document_response_201

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

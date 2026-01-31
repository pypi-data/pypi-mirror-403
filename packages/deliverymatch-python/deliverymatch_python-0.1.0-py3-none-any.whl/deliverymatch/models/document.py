from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.document_document_type import DocumentDocumentType
from ..models.document_file_type import DocumentFileType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Document")


@_attrs_define
class Document:
    """
    Attributes:
        data (str | Unset): Base64 encoded string
        document_type (DocumentDocumentType | Unset):
        file_type (DocumentFileType | Unset):
    """

    data: str | Unset = UNSET
    document_type: DocumentDocumentType | Unset = UNSET
    file_type: DocumentFileType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data

        document_type: str | Unset = UNSET
        if not isinstance(self.document_type, Unset):
            document_type = self.document_type.value

        file_type: str | Unset = UNSET
        if not isinstance(self.file_type, Unset):
            file_type = self.file_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
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
        data = d.pop("data", UNSET)

        _document_type = d.pop("documentType", UNSET)
        document_type: DocumentDocumentType | Unset
        if isinstance(_document_type, Unset):
            document_type = UNSET
        else:
            document_type = DocumentDocumentType(_document_type)

        _file_type = d.pop("fileType", UNSET)
        file_type: DocumentFileType | Unset
        if isinstance(_file_type, Unset):
            file_type = UNSET
        else:
            file_type = DocumentFileType(_file_type)

        document = cls(
            data=data,
            document_type=document_type,
            file_type=file_type,
        )

        document.additional_properties = d
        return document

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

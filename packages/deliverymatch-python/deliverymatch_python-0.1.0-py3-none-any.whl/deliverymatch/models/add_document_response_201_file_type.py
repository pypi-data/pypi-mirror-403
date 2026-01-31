from enum import Enum


class AddDocumentResponse201FileType(str, Enum):
    PDF = "PDF"
    PNG = "PNG"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class DocumentFileType(str, Enum):
    PDF = "pdf"
    PNG = "png"

    def __str__(self) -> str:
        return str(self.value)

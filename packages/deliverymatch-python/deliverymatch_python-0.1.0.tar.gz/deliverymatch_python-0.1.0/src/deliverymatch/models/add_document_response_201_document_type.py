from enum import Enum


class AddDocumentResponse201DocumentType(str, Enum):
    CMR = "CMR"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    DGD = "DGD"
    EXPORT_DOCUMENT = "EXPORT_DOCUMENT"
    IATA = "IATA"
    PICKLIST = "PICKLIST"
    POD = "POD"

    def __str__(self) -> str:
        return str(self.value)

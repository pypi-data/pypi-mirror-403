from enum import Enum


class UpdateShipmentMethodBodyAction(str, Enum):
    BOOK = "book"

    def __str__(self) -> str:
        return str(self.value)

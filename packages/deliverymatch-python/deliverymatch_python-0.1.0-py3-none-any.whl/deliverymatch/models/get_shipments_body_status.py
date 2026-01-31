from enum import Enum


class GetShipmentsBodyStatus(str, Enum):
    BOOKED = "booked"
    DELETE = "delete"
    DELIVERED = "delivered"
    DRAFT = "draft"
    NEW = "new"

    def __str__(self) -> str:
        return str(self.value)

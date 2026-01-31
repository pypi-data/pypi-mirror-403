from enum import Enum


class Status(str, Enum):
    BOOKED = "booked"
    DELETED = "deleted"
    DELIVERED = "delivered"
    DELIVERY = "delivery"
    DRAFT = "draft"
    HUB = "hub"
    NEW = "new"
    PICKEDUP = "pickedup"

    def __str__(self) -> str:
        return str(self.value)

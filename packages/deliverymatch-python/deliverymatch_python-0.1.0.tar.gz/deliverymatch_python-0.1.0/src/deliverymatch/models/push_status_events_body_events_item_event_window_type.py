from enum import Enum


class PushStatusEventsBodyEventsItemEventWindowType(str, Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"

    def __str__(self) -> str:
        return str(self.value)

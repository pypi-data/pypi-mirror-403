from enum import Enum


class ClientMethod(str, Enum):
    FIRST = "first"
    GREEN = "green"
    LOWPRICE = "lowprice"

    def __str__(self) -> str:
        return str(self.value)

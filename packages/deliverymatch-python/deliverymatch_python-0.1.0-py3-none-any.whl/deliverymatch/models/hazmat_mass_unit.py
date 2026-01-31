from enum import Enum


class HazmatMassUnit(str, Enum):
    G = "G"
    KG = "KG"
    L = "L"

    def __str__(self) -> str:
        return str(self.value)

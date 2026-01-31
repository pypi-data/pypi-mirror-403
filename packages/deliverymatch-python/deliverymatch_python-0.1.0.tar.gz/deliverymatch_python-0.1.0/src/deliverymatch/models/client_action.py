from enum import Enum


class ClientAction(str, Enum):
    BOOK = "book"
    ONLYSHOWCHEAPEST = "onlyshowcheapest"
    PRINT = "print"
    RETURNMAIL = "returnmail"
    SAVE = "save"
    SELECT = "select"
    SELECTBOOK = "selectbook"
    SELECTPRINT = "selectprint"
    SHOW = "show"

    def __str__(self) -> str:
        return str(self.value)

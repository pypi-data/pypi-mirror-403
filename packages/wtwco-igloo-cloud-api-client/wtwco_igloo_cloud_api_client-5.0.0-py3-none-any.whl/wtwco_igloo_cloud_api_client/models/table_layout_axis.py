from enum import Enum


class TableLayoutAxis(str, Enum):
    COLUMN = "Column"
    ROW = "Row"

    def __str__(self) -> str:
        return str(self.value)

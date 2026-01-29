from enum import Enum


class TableReadOnlyReasonV2(str, Enum):
    NONE = "None"
    NOTCALCULATED = "NotCalculated"
    RESULT = "Result"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return str(self.value)

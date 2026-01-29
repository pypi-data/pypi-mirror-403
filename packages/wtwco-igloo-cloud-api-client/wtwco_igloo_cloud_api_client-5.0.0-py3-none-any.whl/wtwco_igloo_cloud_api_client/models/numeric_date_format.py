from enum import Enum


class NumericDateFormat(str, Enum):
    NOTSUPPORTED = "NotSupported"
    OADATE = "OADate"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class MessageType(str, Enum):
    ERROR = "Error"
    INFORMATION = "Information"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)

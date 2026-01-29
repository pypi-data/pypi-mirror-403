from enum import Enum


class RunState(str, Enum):
    COMPLETED = "Completed"
    ERROR = "Error"
    INPROGRESS = "InProgress"
    PROCESSING = "Processing"
    UNCALCULATED = "Uncalculated"
    WARNED = "Warned"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class JobState(str, Enum):
    CANCELLATIONREQUESTED = "CancellationRequested"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
    ERROR = "Error"
    INPROGRESS = "InProgress"
    WARNED = "Warned"

    def __str__(self) -> str:
        return str(self.value)

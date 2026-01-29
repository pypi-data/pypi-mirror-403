from enum import Enum


class RunFinalizationState(str, Enum):
    FINALIZATIONREQUESTED = "FinalizationRequested"
    FINALIZED = "Finalized"
    FINALIZING = "Finalizing"
    NOTFINALIZED = "NotFinalized"

    def __str__(self) -> str:
        return str(self.value)

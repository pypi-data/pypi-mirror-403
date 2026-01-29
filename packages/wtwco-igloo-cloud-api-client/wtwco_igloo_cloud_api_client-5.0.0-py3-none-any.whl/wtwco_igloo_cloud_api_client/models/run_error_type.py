from enum import Enum


class RunErrorType(str, Enum):
    FINALIZATION = "Finalization"
    JOB = "Job"
    TABLECALCULATION = "TableCalculation"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return str(self.value)

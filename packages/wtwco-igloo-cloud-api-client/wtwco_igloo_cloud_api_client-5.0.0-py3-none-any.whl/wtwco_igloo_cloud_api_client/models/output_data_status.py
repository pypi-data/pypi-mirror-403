from enum import Enum


class OutputDataStatus(str, Enum):
    CALCULATING = "Calculating"
    DONE = "Done"
    MODELERROR = "ModelError"

    def __str__(self) -> str:
        return str(self.value)

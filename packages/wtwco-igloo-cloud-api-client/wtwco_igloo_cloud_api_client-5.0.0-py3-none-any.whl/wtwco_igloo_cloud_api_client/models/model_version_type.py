from enum import Enum


class ModelVersionType(str, Enum):
    FINALIZED = "Finalized"
    INDEVELOPMENT = "InDevelopment"
    WTW = "WTW"

    def __str__(self) -> str:
        return str(self.value)

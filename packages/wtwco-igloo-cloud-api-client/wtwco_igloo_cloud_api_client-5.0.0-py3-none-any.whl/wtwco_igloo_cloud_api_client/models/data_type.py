from enum import Enum


class DataType(str, Enum):
    BOOLEAN = "Boolean"
    DATE = "Date"
    FILE = "File"
    ID = "Id"
    INTEGER = "Integer"
    POSITION = "Position"
    REAL = "Real"
    RUNARTIFACT = "RunArtifact"
    STRING = "String"

    def __str__(self) -> str:
        return str(self.value)

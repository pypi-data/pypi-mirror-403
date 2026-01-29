from enum import Enum


class DataTableInclude(str, Enum):
    DATA = "Data"
    DATAANDDEFINITION = "DataAndDefinition"
    DEFINITION = "Definition"

    def __str__(self) -> str:
        return str(self.value)

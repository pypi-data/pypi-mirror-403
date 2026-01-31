from enum import Enum


class Aggregation(str, Enum):
    AVERAGE = "average"
    COUNT = "count"
    MAX = "max"
    SUM = "sum"

    def __str__(self) -> str:
        return str(self.value)

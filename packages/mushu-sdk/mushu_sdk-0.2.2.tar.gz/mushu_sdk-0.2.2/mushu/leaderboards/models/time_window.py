from enum import Enum


class TimeWindow(str, Enum):
    ALL_TIME = "ALL_TIME"
    THIS_MONTH = "THIS_MONTH"
    THIS_WEEK = "THIS_WEEK"
    TODAY = "TODAY"

    def __str__(self) -> str:
        return str(self.value)

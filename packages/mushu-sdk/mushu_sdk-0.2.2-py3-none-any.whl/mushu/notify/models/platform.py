from enum import Enum


class Platform(str, Enum):
    IOS = "ios"
    WATCHOS = "watchos"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class Channel(str, Enum):
    ALL = "all"
    EMAIL = "email"
    PUSH = "push"

    def __str__(self) -> str:
        return str(self.value)

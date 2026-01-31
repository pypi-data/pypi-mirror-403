from enum import Enum


class InviteType(str, Enum):
    EMAIL = "email"
    LINK = "link"

    def __str__(self) -> str:
        return str(self.value)

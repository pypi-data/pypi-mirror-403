from enum import Enum


class EmailDomainStatus(str, Enum):
    FAILED = "failed"
    PENDING = "pending"
    VERIFIED = "verified"

    def __str__(self) -> str:
        return str(self.value)

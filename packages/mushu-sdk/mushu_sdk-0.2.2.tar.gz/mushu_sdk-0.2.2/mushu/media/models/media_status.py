from enum import Enum


class MediaStatus(str, Enum):
    FAILED = "failed"
    PENDING = "pending"
    READY = "ready"
    UPLOADED = "uploaded"

    def __str__(self) -> str:
        return str(self.value)

from enum import Enum


class VideoStatus(str, Enum):
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    UPLOADING = "uploading"

    def __str__(self) -> str:
        return str(self.value)

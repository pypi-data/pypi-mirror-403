from enum import Enum


class MediaType(str, Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    OTHER = "other"
    VIDEO = "video"

    def __str__(self) -> str:
        return str(self.value)

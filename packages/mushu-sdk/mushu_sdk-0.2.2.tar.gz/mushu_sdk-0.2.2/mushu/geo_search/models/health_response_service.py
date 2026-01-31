from enum import Enum


class HealthResponseService(str, Enum):
    MUSHU_GEO_SEARCH = "mushu-geo-search"

    def __str__(self) -> str:
        return str(self.value)

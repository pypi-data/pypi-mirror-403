from enum import Enum


class BillingModel(str, Enum):
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    TIERED = "tiered"
    USAGE_BASED = "usage_based"

    def __str__(self) -> str:
        return str(self.value)

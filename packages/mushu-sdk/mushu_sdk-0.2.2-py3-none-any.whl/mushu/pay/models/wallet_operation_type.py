from enum import Enum


class WalletOperationType(str, Enum):
    CHARGE = "charge"
    DEPOSIT = "deposit"

    def __str__(self) -> str:
        return str(self.value)

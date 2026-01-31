from enum import Enum


class DnsRecordPurpose(str, Enum):
    DKIM = "dkim"

    def __str__(self) -> str:
        return str(self.value)

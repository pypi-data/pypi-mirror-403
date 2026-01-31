from enum import Enum


class AuthProviderType(str, Enum):
    APPLE = "apple"
    FACEBOOK = "facebook"
    GOOGLE = "google"

    def __str__(self) -> str:
        return str(self.value)

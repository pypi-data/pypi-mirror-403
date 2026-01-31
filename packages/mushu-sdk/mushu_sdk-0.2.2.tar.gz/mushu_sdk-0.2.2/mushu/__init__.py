"""Mushu SDK - Python clients for Mushu services."""

from typing import Literal, overload

from mushu.auth.client import Client as AuthClient
from mushu.notify.client import Client as NotifyClient
from mushu.media.client import Client as GeneratedMediaClient
from mushu.pay.client import Client as PayClient
from mushu.core.client import Client as CoreClient
from mushu.usage.client import Client as UsageClient
from mushu.geo.client import Client as GeoClient
from mushu.leaderboards.client import Client as LeaderboardsClient
from mushu.streaks.client import Client as StreaksClient
from mushu.geo_search.client import Client as Geo_searchClient

# Re-export commonly used core models
from mushu.core.models import ValidateApiKeyRequest, ValidateApiKeyResponse

# Hand-written wrapper clients (ergonomic APIs)
from mushu.wrappers import (
    AuthClient as AuthWrapper,
    NotifyClient as NotifyWrapper,
    MediaWrapper,
    MediaClient,
)

# Helper functions for common operations
from mushu.helpers import can_access_org, can_manage_org, is_org_owner, validate_token_async


@overload
def client(
    service: Literal["auth"], base_url: str | None = None, api_key: str | None = None
) -> AuthClient: ...

@overload
def client(
    service: Literal["notify"], base_url: str | None = None, api_key: str | None = None
) -> NotifyClient: ...

@overload
def client(
    service: Literal["media"], base_url: str | None = None, api_key: str | None = None
) -> MediaClient: ...

@overload
def client(
    service: Literal["pay"], base_url: str | None = None, api_key: str | None = None
) -> PayClient: ...

@overload
def client(
    service: Literal["core"], base_url: str | None = None, api_key: str | None = None
) -> CoreClient: ...

@overload
def client(
    service: Literal["usage"], base_url: str | None = None, api_key: str | None = None
) -> UsageClient: ...

@overload
def client(
    service: Literal["geo"], base_url: str | None = None, api_key: str | None = None
) -> GeoClient: ...

@overload
def client(
    service: Literal["leaderboards"], base_url: str | None = None, api_key: str | None = None
) -> LeaderboardsClient: ...

@overload
def client(
    service: Literal["streaks"], base_url: str | None = None, api_key: str | None = None
) -> StreaksClient: ...

@overload
def client(
    service: Literal["geo_search"], base_url: str | None = None, api_key: str | None = None
) -> Geo_searchClient: ...


def client(service: str, base_url: str | None = None, api_key: str | None = None):
    """Factory to get a typed client for any Mushu service.

    Args:
        service: Service name (auth, notify, media, pay, etc.)
        base_url: Override the default service URL
        api_key: API key — sets the X-API-Key header automatically
    """
    clients = {
        "auth": (AuthClient, "https://auth.mushucorp.com"),
        "notify": (NotifyClient, "https://notify.mushucorp.com"),
        "media": (GeneratedMediaClient, "https://media.mushucorp.com"),
        "pay": (PayClient, "https://pay.mushucorp.com"),
        "core": (CoreClient, "https://core.mushucorp.com"),
        "usage": (UsageClient, "https://usage.mushucorp.com"),
        "geo": (GeoClient, "https://geo.mushucorp.com"),
        "leaderboards": (LeaderboardsClient, "https://leaderboards.mushucorp.com"),
        "streaks": (StreaksClient, "https://streaks.mushucorp.com"),
        "geo_search": (Geo_searchClient, "https://geo_search.mushucorp.com"),
    }
    if service not in clients:
        raise ValueError(f"Unknown service: {service}")
    cls, default_url = clients[service]
    url = base_url or default_url
    generated = cls(base_url=url)

    if api_key:
        generated = generated.with_headers({"X-API-Key": api_key})

    if service == "media":
        return MediaClient(api=generated, api_key=api_key, base_url=url)

    return generated


__all__ = [
    "client",
    # Generated clients (low-level)
    "AuthClient",
    "NotifyClient",
    "GeneratedMediaClient",
    "PayClient",
    "CoreClient",
    "UsageClient",
    "GeoClient",
    "LeaderboardsClient",
    "StreaksClient",
    "Geo_searchClient",
    # Wrapper clients (ergonomic APIs)
    "AuthWrapper",
    "NotifyWrapper",
    "MediaWrapper",
    # Unified clients
    "MediaClient",
    # Core models
    "ValidateApiKeyRequest",
    "ValidateApiKeyResponse",
    # Helper functions
    "validate_token_async",
    "can_manage_org",
    "can_access_org",
    "is_org_owner",
]
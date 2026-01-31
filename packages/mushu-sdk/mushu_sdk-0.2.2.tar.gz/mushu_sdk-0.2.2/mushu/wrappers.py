"""
Hand-written wrapper clients for Mushu services.

These provide simple async methods for common operations until
generated clients are available for all services.

Usage:
    from mushu import AuthClient, NotifyClient

    # Auth client (validate user Bearer tokens)
    auth = AuthClient(auth_url="https://auth.mushucorp.com")
    user = await auth.validate_token(token)

    # Notify client (push/email notifications)
    notify = NotifyClient(api_key="key", app_id="app")
    await notify.send_email(user_id="user_1", subject="Hello", body_html="<p>Hi</p>")
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Auth Client - Token validation and org membership
# =============================================================================


class OrgRole(str, Enum):
    """Organization member role."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


@dataclass
class AuthUser:
    """Authenticated user from mushu-auth."""

    user_id: str
    user_type: str
    email: str | None = None


@dataclass
class OrgMembership:
    """User's membership in an organization."""

    org_id: str
    user_id: str
    role: OrgRole


class AuthClient:
    """
    Client for mushu-auth service.
    Used to validate user tokens and check org membership.
    """

    def __init__(self, auth_url: str):
        self.auth_url = auth_url.rstrip("/")

    async def validate_token(self, token: str) -> AuthUser | None:
        """
        Validate a user token with mushu-auth.

        Args:
            token: Bearer token to validate

        Returns:
            AuthUser if valid, None if invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_url}/auth/validate",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )

            if response.status_code != 200:
                return None

            data = response.json()
            if not data.get("valid"):
                return None

            return AuthUser(
                user_id=data["user_id"],
                user_type=data["user_type"],
                email=data.get("email"),
            )

        except httpx.RequestError as e:
            logger.error(f"Error validating token with mushu-auth: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            return None

    async def get_org_membership(self, token: str, org_id: str) -> OrgMembership | None:
        """
        Get user's membership in an organization.

        Args:
            token: Bearer token
            org_id: Organization ID to check

        Returns:
            OrgMembership if user is a member, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_url}/orgs/{org_id}/members/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )

            if response.status_code == 404:
                return None
            if response.status_code != 200:
                logger.warning(f"Unexpected status checking org membership: {response.status_code}")
                return None

            data = response.json()
            return OrgMembership(
                org_id=data["org_id"],
                user_id=data["user_id"],
                role=OrgRole(data["role"]),
            )

        except httpx.RequestError as e:
            logger.error(f"Error checking org membership: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking org membership: {e}")
            return None

    async def can_access_org(self, token: str, org_id: str) -> bool:
        """Check if user can access an organization (any member)."""
        membership = await self.get_org_membership(token, org_id)
        return membership is not None

    async def can_manage_org(self, token: str, org_id: str) -> bool:
        """Check if user can manage an organization (admin/owner only)."""
        membership = await self.get_org_membership(token, org_id)
        if membership and membership.role in (OrgRole.ADMIN, OrgRole.OWNER):
            return True
        return False

    async def is_org_owner(self, token: str, org_id: str) -> bool:
        """Check if user is the owner of an organization."""
        membership = await self.get_org_membership(token, org_id)
        return membership is not None and membership.role == OrgRole.OWNER


# =============================================================================
# Notify Client - Push notifications and email
# =============================================================================


@dataclass
class NotifyResult:
    """Result of a notification operation."""

    success: bool
    message_id: str | None = None
    error: str | None = None


@dataclass
class NotifyClient:
    """Client for the Notify service.

    Sends push notifications and emails via mushu-notify.
    """

    api_key: str
    app_id: str
    base_url: str = "https://notify.mushucorp.com"
    timeout: float = 10.0

    @property
    def enabled(self) -> bool:
        """Check if client is properly configured."""
        return bool(self.api_key and self.app_id)

    async def send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> NotifyResult:
        """Send a push notification to a user.

        Args:
            user_id: User ID to send to
            title: Notification title
            body: Notification body
            data: Optional data payload

        Returns:
            NotifyResult with success status
        """
        if not self.enabled:
            return NotifyResult(success=False, error="NotifyClient not configured")

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/push/send",
                    json={
                        "app_id": self.app_id,
                        "user_id": user_id,
                        "title": title,
                        "body": body,
                        "data": data or {},
                    },
                    headers={"X-API-Key": self.api_key},
                )

                if response.status_code >= 400:
                    return NotifyResult(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                result = response.json()
                return NotifyResult(
                    success=True,
                    message_id=result.get("message_id"),
                )

        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return NotifyResult(success=False, error=str(e))

    async def send_email(
        self,
        user_id: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> NotifyResult:
        """Send an email to a user.

        Args:
            user_id: User ID to send to (email looked up from user record)
            subject: Email subject
            body_html: HTML body
            body_text: Optional plain text body

        Returns:
            NotifyResult with success status
        """
        if not self.enabled:
            return NotifyResult(success=False, error="NotifyClient not configured")

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/email/send",
                    json={
                        "app_id": self.app_id,
                        "user_id": user_id,
                        "subject": subject,
                        "body_html": body_html,
                        "body_text": body_text,
                    },
                    headers={"X-API-Key": self.api_key},
                )

                if response.status_code >= 400:
                    return NotifyResult(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                    )

                result = response.json()
                return NotifyResult(
                    success=True,
                    message_id=result.get("message_id"),
                )

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return NotifyResult(success=False, error=str(e))


# =============================================================================
# Media Client - Image/video storage and transforms
# =============================================================================

# Default images worker URL
IMAGES_BASE_URL = "https://images.mushucorp.com"


@dataclass
class MediaWrapper:
    """Low-level media client using httpx directly.

    Prefer using MediaClient (returned by mushu.client("media")) instead.
    """

    api_key: str
    base_url: str = "https://media.mushucorp.com"
    images_url: str = IMAGES_BASE_URL
    timeout: float = 30.0

    def get_transform_url(
        self,
        key: str,
        *,
        width: int,
        height: int | None = None,
        fit: str = "cover",
        gravity: str = "auto",
        quality: int = 85,
    ) -> str:
        """Build a custom transform URL for an image.

        Args:
            key: The media storage key (from media item)
            width: Width in pixels (1-2000)
            height: Height in pixels (1-2000), omit to maintain aspect ratio
            fit: How to fit image - cover, contain, scale-down, crop
            gravity: Focus point - auto, face, center
            quality: Output quality 1-100

        Returns:
            Transform URL for the image

        Example:
            # 128x128 avatar with face detection
            url = client.get_transform_url(key, width=128, height=128, gravity="face")
        """
        params = [f"w={width}"]
        if height:
            params.append(f"h={height}")
        if fit != "cover":
            params.append(f"fit={fit}")
        if gravity != "auto":
            params.append(f"gravity={gravity}")
        if quality != 85:
            params.append(f"q={quality}")

        query = "&".join(params)
        return f"{self.images_url}/t/custom/{key}?{query}"

    def get_variant_url(self, key: str, variant: str = "medium") -> str:
        """Get URL for a named variant.

        Args:
            key: The media storage key
            variant: One of original, thumbnail, small, medium, large

        Returns:
            Variant URL for the image
        """
        return f"{self.images_url}/t/{variant}/{key}"

    async def get_upload_url(
        self,
        org_id: str,
        filename: str,
        content_type: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a presigned URL for uploading media.

        Args:
            org_id: Organization ID
            filename: Original filename
            content_type: MIME type (e.g., image/jpeg)
            tenant_id: Optional tenant ID

        Returns:
            Dict with upload_url, media_id, key
        """
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/media/upload-url",
                    json={
                        "org_id": org_id,
                        "tenant_id": tenant_id,
                        "filename": filename,
                        "content_type": content_type,
                    },
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get upload URL: {e.response.text}") from e

    async def confirm_upload(self, media_id: str) -> dict[str, Any]:
        """Confirm that an upload has completed.

        Args:
            media_id: The media ID from get_upload_url

        Returns:
            Confirmed media item
        """
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    f"/media/{media_id}/confirm",
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to confirm upload: {e.response.text}") from e

    async def get_image_urls(self, media_id: str) -> dict[str, str]:
        """Get all variant URLs for an image.

        Args:
            media_id: The media ID

        Returns:
            Dict with original, thumbnail, small, medium, large URLs
        """
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.get(
                    f"/media/{media_id}/images",
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get image URLs: {e.response.text}") from e


# =============================================================================
# Unified Media Client - Generated client + transform helpers
# =============================================================================


@dataclass
class MediaClient:
    """Unified client for the Media service.

    Combines the generated API client with transform URL helpers
    and convenience async methods.

    Returned by ``mushu.client("media", api_key="msk_...")``.

    Usage::

        media = mushu.client("media", api_key="msk_xxx")

        # URL helpers (no API call)
        url = media.get_variant_url("org/key", "thumbnail")
        url = media.get_transform_url("org/key", width=128, gravity="face")

        # Convenience async methods
        upload = await media.get_upload_url("org_1", "photo.jpg", "image/jpeg")

        # Access generated client for advanced use
        from mushu.media.api.media import get_upload_url
        await get_upload_url.asyncio_detailed(client=media.api, body=...)
    """

    api: Any  # Generated media Client
    api_key: str | None = None
    base_url: str = "https://media.mushucorp.com"
    images_url: str = IMAGES_BASE_URL
    timeout: float = 30.0

    def get_transform_url(
        self,
        key: str,
        *,
        width: int,
        height: int | None = None,
        fit: str = "cover",
        gravity: str = "auto",
        quality: int = 85,
    ) -> str:
        """Build a custom transform URL for an image.

        Args:
            key: The media storage key (from media item)
            width: Width in pixels (1-2000)
            height: Height in pixels (1-2000), omit to maintain aspect ratio
            fit: How to fit image - cover, contain, scale-down, crop
            gravity: Focus point - auto, face, center
            quality: Output quality 1-100

        Returns:
            Transform URL for the image
        """
        params = [f"w={width}"]
        if height:
            params.append(f"h={height}")
        if fit != "cover":
            params.append(f"fit={fit}")
        if gravity != "auto":
            params.append(f"gravity={gravity}")
        if quality != 85:
            params.append(f"q={quality}")

        query = "&".join(params)
        return f"{self.images_url}/t/custom/{key}?{query}"

    def get_variant_url(self, key: str, variant: str = "medium") -> str:
        """Get URL for a named variant.

        Args:
            key: The media storage key
            variant: One of original, thumbnail, small, medium, large

        Returns:
            Variant URL for the image
        """
        return f"{self.images_url}/t/{variant}/{key}"

    async def get_upload_url(
        self,
        org_id: str,
        filename: str,
        content_type: str,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a presigned URL for uploading media."""
        if not self.api_key:
            raise RuntimeError("api_key is required for get_upload_url")
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/media/upload-url",
                    json={
                        "org_id": org_id,
                        "tenant_id": tenant_id,
                        "filename": filename,
                        "content_type": content_type,
                    },
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get upload URL: {e.response.text}") from e

    async def confirm_upload(self, media_id: str) -> dict[str, Any]:
        """Confirm that an upload has completed."""
        if not self.api_key:
            raise RuntimeError("api_key is required for confirm_upload")
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.post(
                    f"/media/{media_id}/confirm",
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to confirm upload: {e.response.text}") from e

    async def get_image_urls(self, media_id: str) -> dict[str, str]:
        """Get all variant URLs for an image."""
        if not self.api_key:
            raise RuntimeError("api_key is required for get_image_urls")
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.get(
                    f"/media/{media_id}/images",
                    headers={"X-API-Key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get image URLs: {e.response.text}") from e
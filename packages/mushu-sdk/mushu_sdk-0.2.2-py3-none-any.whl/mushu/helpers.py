"""
Helper functions for common Mushu SDK operations.

These provide simple async wrappers around generated client calls
for common patterns like token validation and org membership checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mushu.auth.client import Client as AuthClient
    from mushu.auth.models import ValidateTokenResponse
    from mushu.core.client import Client as CoreClient


async def validate_token_async(
    auth_client: AuthClient,
    token: str,
) -> ValidateTokenResponse | None:
    """
    Validate a token using the generated auth client.

    Args:
        auth_client: Generated auth service client
        token: Bearer token to validate (without "Bearer " prefix)

    Returns:
        ValidateTokenResponse if valid, None if invalid or error
    """
    from mushu.auth.api.auth import validate_token
    from mushu.auth.models import HTTPValidationError

    response = await validate_token.asyncio(
        client=auth_client,
        authorization=f"Bearer {token}",
    )
    if response is None or isinstance(response, HTTPValidationError):
        return None
    if response.valid:
        return response
    return None


async def can_manage_org(
    core_client: CoreClient,
    token: str,
    org_id: str,
) -> bool:
    """
    Check if user can manage an org (admin/owner only).

    Args:
        core_client: Generated core service client
        token: Bearer token (without "Bearer " prefix)
        org_id: Organization ID to check

    Returns:
        True if user is admin or owner, False otherwise
    """
    from mushu.core.api.orgs import get_my_membership
    from mushu.core.models import HTTPValidationError, OrgRole

    membership = await get_my_membership.asyncio(
        org_id=org_id,
        client=core_client,
        authorization=f"Bearer {token}",
    )
    if membership is None or isinstance(membership, HTTPValidationError):
        return False
    return membership.role in (OrgRole.ADMIN, OrgRole.OWNER)


async def can_access_org(
    core_client: CoreClient,
    token: str,
    org_id: str,
) -> bool:
    """
    Check if user can access an org (any member).

    Args:
        core_client: Generated core service client
        token: Bearer token (without "Bearer " prefix)
        org_id: Organization ID to check

    Returns:
        True if user is a member, False otherwise
    """
    from mushu.core.api.orgs import get_my_membership
    from mushu.core.models import HTTPValidationError

    membership = await get_my_membership.asyncio(
        org_id=org_id,
        client=core_client,
        authorization=f"Bearer {token}",
    )
    if membership is None or isinstance(membership, HTTPValidationError):
        return False
    return True


async def is_org_owner(
    core_client: CoreClient,
    token: str,
    org_id: str,
) -> bool:
    """
    Check if user is the owner of an org.

    Args:
        core_client: Generated core service client
        token: Bearer token (without "Bearer " prefix)
        org_id: Organization ID to check

    Returns:
        True if user is owner, False otherwise
    """
    from mushu.core.api.orgs import get_my_membership
    from mushu.core.models import HTTPValidationError, OrgRole

    membership = await get_my_membership.asyncio(
        org_id=org_id,
        client=core_client,
        authorization=f"Bearer {token}",
    )
    if membership is None or isinstance(membership, HTTPValidationError):
        return False
    return membership.role == OrgRole.OWNER

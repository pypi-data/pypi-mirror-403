"""Firebase authentication middleware for FastAPI.

Supports two authentication methods:
1. Firebase ID tokens (from web app)
2. Google OAuth access tokens (from CLI)
"""

import logging
import os
from typing import Annotated, Literal

import httpx
from fastapi import Depends, HTTPException, Header, status
from pydantic import BaseModel
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

logger = logging.getLogger(__name__)

# Valid org roles
OrgRole = Literal["owner", "admin", "member", "viewer"]
VALID_ROLES = {"owner", "admin", "member", "viewer"}

# Initialize Firebase Admin SDK
# In production: uses Application Default Credentials
# In development: connects to emulator if FIREBASE_AUTH_EMULATOR_HOST is set
_firebase_app = None


def _init_firebase():
    """Initialize Firebase Admin SDK (lazy initialization)."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    # Check if running with emulator
    emulator_host = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST")
    env = os.environ.get("ENV", "production").lower()

    if emulator_host:
        # Only allow emulator in dev/test environments
        if env not in ("development", "dev", "test", "local"):
            raise RuntimeError(
                f"FIREBASE_AUTH_EMULATOR_HOST is set but ENV={env}. "
                "Emulator is only allowed in dev/test environments."
            )
        logger.info(f"Using Firebase Auth Emulator: {emulator_host}")
        _firebase_app = firebase_admin.initialize_app(
            options={"projectId": "metricly-dev"}
        )
    else:
        # Production: use Application Default Credentials
        logger.info("Using Firebase Auth (production)")
        cred = credentials.ApplicationDefault()
        _firebase_app = firebase_admin.initialize_app(cred)

    return _firebase_app


class AuthenticatedUser(BaseModel):
    """Authenticated user with org context from Firebase token claims."""

    uid: str
    email: str | None = None
    name: str | None = None
    org_id: str
    org_role: OrgRole


def verify_firebase_token(authorization: str) -> dict:
    """Verify Firebase ID token and return decoded claims.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token is invalid or missing
    """
    app = _init_firebase()

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        # Verify the token against the initialized app
        # check_revoked=True ensures revoked tokens are rejected
        decoded = firebase_auth.verify_id_token(token, check_revoked=True, app=app)
        return decoded
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.InvalidIdTokenError as e:
        # Log the actual error but don't expose details to client
        logger.warning(f"Invalid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Log unexpected errors but don't expose details
        logger.error(f"Token verification error: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """FastAPI dependency to get authenticated user from Firebase token.

    Extracts user info and org context from custom claims.

    Usage:
        @app.get("/protected")
        async def protected_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
            return {"org_id": user.org_id}
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = verify_firebase_token(authorization)

    # Extract org context from custom claims
    current_org = claims.get("currentOrg")
    orgs = claims.get("orgs", {})

    if not current_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organization selected. Please select an organization.",
        )

    if current_org not in orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization.",
        )

    # Validate and normalize role
    raw_role = orgs.get(current_org, "viewer")
    if raw_role not in VALID_ROLES:
        logger.warning(f"Unknown role '{raw_role}' for user {claims.get('uid')} in org {current_org}")
        raw_role = "viewer"  # Default to most restrictive role

    return AuthenticatedUser(
        uid=claims["uid"],
        email=claims.get("email"),
        name=claims.get("name"),
        org_id=current_org,
        org_role=raw_role,
    )


async def verify_oauth_token(token: str) -> dict:
    """Verify Google OAuth access token by calling userinfo endpoint.

    Args:
        token: Google OAuth access token

    Returns:
        User info dict with email, name, etc.

    Raises:
        HTTPException: If token is invalid
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token}"},
        )

        if resp.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OAuth token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if resp.status_code != 200:
            logger.warning(f"OAuth userinfo failed: {resp.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to verify OAuth token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return resp.json()


async def get_current_user_flexible(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Get authenticated user, supporting both Firebase and OAuth tokens.

    Tries Firebase ID token first (for web app), falls back to Google OAuth
    token (for CLI). This allows both authentication methods to work.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Try Firebase ID token first
    try:
        return await get_current_user(authorization)
    except HTTPException as e:
        if e.status_code != 401:
            raise
        # Firebase auth failed, try OAuth
        logger.debug("Firebase auth failed, trying OAuth")

    # Try Google OAuth token - verify with Google's userinfo endpoint
    user_info = await verify_oauth_token(token)
    email = user_info.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found in OAuth token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up user context from Firestore
    from services.auth import get_user_by_email

    try:
        user_context = get_user_by_email(email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    return AuthenticatedUser(
        uid=user_context.uid,
        email=user_context.email,
        name=user_info.get("name"),
        org_id=user_context.org_id,
        org_role=user_context.role,
    )


def require_org_role(*allowed_roles: str):
    """Dependency factory to require specific org roles.

    Usage:
        @app.put("/api/dashboard")
        async def update_dashboard(
            user: AuthenticatedUser = Depends(require_org_role("owner", "admin"))
        ):
            ...
    """

    async def check_role(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if user.org_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return user

    return check_role

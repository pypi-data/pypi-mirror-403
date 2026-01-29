"""Authentication and authorization services.

Provides user context management, role-based access control, and
Firestore user lookup functions used across MCP, CLI, and chat.
"""

from dataclasses import dataclass
from typing import Literal

from google.cloud import firestore


# Role hierarchy - higher number = more permissions
ROLE_HIERARCHY: dict[str, int] = {
    "owner": 4,
    "admin": 3,
    "member": 2,
    "viewer": 1,
}

Role = Literal["owner", "admin", "member", "viewer"]


@dataclass
class UserContext:
    """Authenticated user context for service requests.

    Attributes:
        uid: Firestore user document ID
        email: User's email address (from OAuth)
        org_id: Current organization ID
        role: User's role in the organization
    """

    uid: str
    email: str
    org_id: str
    role: Role


def require_role(user: UserContext, minimum: Role) -> None:
    """Check if user has at least the required role.

    Args:
        user: Authenticated user context
        minimum: Minimum required role

    Raises:
        PermissionError: If user's role is insufficient
    """
    user_level = ROLE_HIERARCHY.get(user.role, 0)
    required_level = ROLE_HIERARCHY.get(minimum, 0)

    if user_level < required_level:
        raise PermissionError(
            f"Requires {minimum} role, you have {user.role}"
        )


def _get_firestore_client() -> firestore.Client:
    """Get Firestore client (allows mocking in tests)."""
    return firestore.Client()


def get_user_by_email(email: str) -> UserContext:
    """Look up user by email and return their context.

    Args:
        email: User's email address

    Returns:
        UserContext with user info and current org

    Raises:
        ValueError: If user not found or has no org membership
    """
    db = _get_firestore_client()

    # Look up user by email
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).limit(1)
    users = list(query.stream())

    if not users:
        raise ValueError(f"User with email {email} not found")

    user_doc = users[0]
    user_data = user_doc.to_dict()
    user_id = user_doc.id

    # Get org memberships from user document
    orgs = user_data.get("orgs", {})
    current_org = user_data.get("currentOrg")

    if not orgs:
        raise ValueError("User is not a member of any organization")

    # Use currentOrg if set, otherwise use first org
    if not current_org or current_org not in orgs:
        current_org = next(iter(orgs.keys()))

    raw_role = orgs.get(current_org, "viewer")
    if raw_role not in ROLE_HIERARCHY:
        raw_role = "viewer"

    return UserContext(
        uid=user_id,
        email=email,
        org_id=current_org,
        role=raw_role,
    )


def get_user_orgs(email: str) -> list[dict]:
    """Get list of organizations the user belongs to.

    Args:
        email: User's email address

    Returns:
        List of org info dicts with id, name, and role

    Raises:
        ValueError: If user not found
    """
    db = _get_firestore_client()

    # Look up user by email
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).limit(1)
    users = list(query.stream())

    if not users:
        raise ValueError(f"User with email {email} not found")

    user_data = users[0].to_dict()
    orgs = user_data.get("orgs", {})
    current_org = user_data.get("currentOrg")

    result = []
    for org_id, role in orgs.items():
        # Fetch org name from orgs collection
        org_doc = db.collection("orgs").document(org_id).get()
        org_name = org_id  # Default to ID if doc doesn't exist
        if org_doc.exists:
            org_data = org_doc.to_dict()
            org_name = org_data.get("name", org_id)

        result.append({
            "id": org_id,
            "name": org_name,
            "role": role if role in ROLE_HIERARCHY else "viewer",
            "current": org_id == current_org,
        })

    return result


def switch_org(email: str, org_id: str) -> UserContext:
    """Switch user's current organization.

    Args:
        email: User's email address
        org_id: Organization ID to switch to

    Returns:
        Updated UserContext with new org

    Raises:
        ValueError: If user not found or not a member of the org
    """
    db = _get_firestore_client()

    # Look up user by email
    users_ref = db.collection("users")
    query = users_ref.where("email", "==", email).limit(1)
    users = list(query.stream())

    if not users:
        raise ValueError(f"User with email {email} not found")

    user_doc = users[0]
    user_data = user_doc.to_dict()
    user_id = user_doc.id

    # Verify user is member of the org
    orgs = user_data.get("orgs", {})
    if org_id not in orgs:
        raise ValueError(f"User is not a member of organization {org_id}")

    # Update currentOrg in Firestore
    users_ref.document(user_id).update({"currentOrg": org_id})

    raw_role = orgs.get(org_id, "viewer")
    if raw_role not in ROLE_HIERARCHY:
        raw_role = "viewer"

    return UserContext(
        uid=user_id,
        email=email,
        org_id=org_id,
        role=raw_role,
    )

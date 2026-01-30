"""Authentication and authorization services.

Provides user context management, role-based access control, and
Firestore user lookup functions used across MCP, CLI, and chat.

Data Model (matches Cloud Functions and React app):
- Users: users/{uid} with defaultOrgId field
- Organizations: organizations/{orgId}
- Membership: organizations/{orgId}/members/{uid} with role field
"""

from dataclasses import dataclass
from typing import Literal

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


# Firestore collection names - must match Cloud Functions
USERS_COLLECTION = "users"
ORGANIZATIONS_COLLECTION = "organizations"
MEMBERS_SUBCOLLECTION = "members"

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
        org_name: Current organization name
        role: User's role in the organization
    """

    uid: str
    email: str
    org_id: str
    org_name: str
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
    return firestore.Client(project="metricly-dev")


def get_user_by_email(email: str) -> UserContext:
    """Look up user by email and return their context.

    Uses the same data model as Cloud Functions and React app:
    - User document has defaultOrgId field
    - Membership role is in organizations/{orgId}/members/{uid}

    Args:
        email: User's email address

    Returns:
        UserContext with user info and current org

    Raises:
        ValueError: If user not found or has no org membership
    """
    db = _get_firestore_client()

    # Look up user by email
    users_ref = db.collection(USERS_COLLECTION)
    query = users_ref.where(filter=FieldFilter("email", "==", email)).limit(1)
    users = list(query.stream())

    if not users:
        raise ValueError(f"User with email {email} not found")

    user_doc = users[0]
    user_data = user_doc.to_dict()
    user_id = user_doc.id

    # Get current org from defaultOrgId field
    current_org = user_data.get("defaultOrgId")
    if not current_org:
        raise ValueError("User has no default organization set")

    # Look up org document and membership
    org_ref = db.collection(ORGANIZATIONS_COLLECTION).document(current_org)
    org_doc = org_ref.get()

    if not org_doc.exists:
        raise ValueError(f"Organization {current_org} not found")

    org_data = org_doc.to_dict()
    org_name = org_data.get("name", current_org)

    # Look up role from membership subcollection
    member_doc = org_ref.collection(MEMBERS_SUBCOLLECTION).document(user_id).get()

    if not member_doc.exists:
        raise ValueError(f"User is not a member of organization {current_org}")

    member_data = member_doc.to_dict()
    raw_role = member_data.get("role", "viewer")
    if raw_role not in ROLE_HIERARCHY:
        raw_role = "viewer"

    return UserContext(
        uid=user_id,
        email=email,
        org_id=current_org,
        org_name=org_name,
        role=raw_role,
    )


def get_user_orgs(email: str) -> list[dict]:
    """Get list of organizations the user belongs to.

    Uses collection group query on members subcollection to find all orgs.

    Args:
        email: User's email address

    Returns:
        List of org info dicts with id, name, and role

    Raises:
        ValueError: If user not found
    """
    db = _get_firestore_client()

    # Look up user by email
    users_ref = db.collection(USERS_COLLECTION)
    query = users_ref.where(filter=FieldFilter("email", "==", email)).limit(1)
    users = list(query.stream())

    if not users:
        raise ValueError(f"User with email {email} not found")

    user_doc = users[0]
    user_data = user_doc.to_dict()
    user_id = user_doc.id
    current_org = user_data.get("defaultOrgId")

    # Use collection group query to find all memberships
    # Query by uid field in membership documents
    memberships = db.collection_group(MEMBERS_SUBCOLLECTION) \
        .where(filter=FieldFilter("uid", "==", user_id)) \
        .stream()

    result = []
    for member_doc in memberships:
        # Extract org_id from path: organizations/{org_id}/members/{user_id}
        path_parts = member_doc.reference.path.split("/")
        if len(path_parts) >= 2 and path_parts[0] == ORGANIZATIONS_COLLECTION:
            org_id = path_parts[1]
            member_data = member_doc.to_dict()

            # Fetch org name
            org_doc = db.collection(ORGANIZATIONS_COLLECTION).document(org_id).get()
            org_name = org_id
            if org_doc.exists:
                org_data = org_doc.to_dict()
                org_name = org_data.get("name", org_id)

            raw_role = member_data.get("role", "viewer")
            if raw_role not in ROLE_HIERARCHY:
                raw_role = "viewer"

            result.append({
                "id": org_id,
                "name": org_name,
                "role": raw_role,
                "current": org_id == current_org,
            })

    if not result:
        raise ValueError("User is not a member of any organization")

    return result


def switch_org(email: str, org_id: str) -> UserContext:
    """Switch user's current organization.

    Updates defaultOrgId in user document.

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
    users_ref = db.collection(USERS_COLLECTION)
    query = users_ref.where(filter=FieldFilter("email", "==", email)).limit(1)
    users = list(query.stream())

    if not users:
        raise ValueError(f"User with email {email} not found")

    user_doc = users[0]
    user_id = user_doc.id

    # Look up org and verify membership
    org_ref = db.collection(ORGANIZATIONS_COLLECTION).document(org_id)
    org_doc = org_ref.get()

    if not org_doc.exists:
        raise ValueError(f"Organization {org_id} not found")

    org_data = org_doc.to_dict()
    org_name = org_data.get("name", org_id)

    member_doc = org_ref.collection(MEMBERS_SUBCOLLECTION).document(user_id).get()

    if not member_doc.exists:
        raise ValueError(f"User is not a member of organization {org_id}")

    member_data = member_doc.to_dict()
    raw_role = member_data.get("role", "viewer")
    if raw_role not in ROLE_HIERARCHY:
        raw_role = "viewer"

    # Update defaultOrgId in user document
    users_ref.document(user_id).update({"defaultOrgId": org_id})

    return UserContext(
        uid=user_id,
        email=email,
        org_id=org_id,
        org_name=org_name,
        role=raw_role,
    )

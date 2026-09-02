from rest_framework.permissions import BasePermission


ROLE_ADMIN = "ADMIN"
ROLE_OPERATIONS = "OPERATIONS"
ROLE_READ_ONLY = "READ_ONLY"


READ_ROLES = {
    ROLE_ADMIN,
    ROLE_OPERATIONS,
    ROLE_READ_ONLY,
}

WRITE_ROLES = {
    ROLE_ADMIN,
    ROLE_OPERATIONS,
}


class CustomerAccessPermission(BasePermission):
    """
    Authorization policy for customer API operations.

    Authentication is handled by DRF's global authentication policy.
    This class evaluates application-level role permissions.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_roles = set(
            request.user.groups.values_list("name", flat=True)
        )

        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return bool(user_roles & READ_ROLES)

        if request.method == "POST":
            return bool(user_roles & WRITE_ROLES)

        return False

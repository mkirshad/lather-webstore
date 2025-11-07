from __future__ import annotations

from typing import Iterable, Sequence

from rest_framework import permissions


class HasTenantPermissions(permissions.BasePermission):
    """Enforces tenant-scoped permission codes resolved from memberships."""

    message = "You do not have permission to perform this action within the tenant."

    def has_permission(self, request, view) -> bool:
        required: Sequence[str] = tuple(getattr(view, "required_permissions", ()))
        if not required:
            return True

        membership = getattr(request, "membership", None)
        if membership is None:
            return False

        membership_codes: Iterable[str] = getattr(membership, "permission_codes", [])
        membership_set = set(membership_codes)
        return all(code in membership_set for code in required)


def require_tenant_permissions(*permission_codes: str):
    """Class decorator/helper to declare tenant permissions on API views."""

    def decorator(view_cls):
        setattr(view_cls, "required_permissions", permission_codes)
        return view_cls

    return decorator

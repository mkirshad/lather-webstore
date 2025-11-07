from __future__ import annotations

from contextlib import contextmanager
from typing import Optional
from uuid import UUID

from django.db import connection

_current_tenant: Optional[str] = None


def _normalize_tenant_id(tenant: object | None) -> Optional[str]:
    if tenant is None:
        return None
    if isinstance(tenant, UUID):
        return str(tenant)
    if hasattr(tenant, "id"):
        return str(getattr(tenant, "id"))
    if isinstance(tenant, str):
        return tenant
    raise TypeError("Unsupported tenant identifier type")


def _set_pg_tenant(tenant_id: Optional[str]) -> None:
    if connection.vendor != "postgresql":  # Skip when not using Postgres
        return
    value = tenant_id or ""
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.tenant_id', %s, false)", [value])


def set_current_tenant(tenant: object | None) -> Optional[str]:
    global _current_tenant
    tenant_id = _normalize_tenant_id(tenant)
    previous = _current_tenant
    _current_tenant = tenant_id
    _set_pg_tenant(tenant_id)
    return previous


def restore_previous_tenant(previous: Optional[str]) -> None:
    global _current_tenant
    _current_tenant = previous
    _set_pg_tenant(previous)


@contextmanager
def activate_tenant(tenant: object | None):
    previous = set_current_tenant(tenant)
    try:
        yield
    finally:
        restore_previous_tenant(previous)


def get_current_tenant_id() -> Optional[str]:
    return _current_tenant

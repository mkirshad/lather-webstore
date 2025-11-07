from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from rest_framework import exceptions as drf_exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import AuditLog, Membership, Tenant
from .tenant import activate_tenant


class CurrentTenantMiddleware:
    """Attach tenant context to each request and set the Postgres session GUC."""

    header_keys = ("HTTP_X_TENANT", "HTTP_X_TENANT_ID")

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    def __call__(self, request):
        tenant_identifier = self._extract_header(request)
        tenant = None
        if tenant_identifier:
            try:
                tenant = Tenant.objects.get(slug__iexact=tenant_identifier)
            except Tenant.DoesNotExist:
                return JsonResponse(
                    {
                        "detail": "Unknown tenant identifier. Double-check the X-Tenant header or create the tenant first.",
                    },
                    status=400,
                )
            tenant.ensure_system_roles()

        request.tenant = tenant
        request.membership = None

        self._ensure_authenticated_user(request)

        with activate_tenant(tenant):
            if tenant and request.user.is_authenticated:
                membership = (
                    Membership.objects.select_related("tenant", "role")
                    .filter(tenant=tenant, user=request.user, status=Membership.Status.ACTIVE)
                    .first()
                )
                if membership is None:
                    raise PermissionDenied("You do not have access to this tenant.")
                request.membership = membership

            response = self.get_response(request)

        return response

    def _extract_header(self, request) -> str | None:
        for key in self.header_keys:
            value = request.META.get(key)
            if value:
                return value.strip()
        return None

    def _ensure_authenticated_user(self, request) -> None:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            return

        try:
            authenticated = self.jwt_authentication.authenticate(request)
        except drf_exceptions.AuthenticationFailed:
            authenticated = None

        if not authenticated:
            return

        user, token = authenticated
        request.user = user
        request.auth = token
        # Align with AuthenticationMiddleware expectations so future accesses reuse the user.
        request._cached_user = user
        request._cached_auth = token


class AuditLogMiddleware:
    """Persist CRUD actions, sign-ins, and sign-outs to the audit log."""

    tracked_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("irshados.audit")

    def __call__(self, request):
        should_track = request.method in self.tracked_methods or getattr(
            request, "audit_always", False
        )
        request_payload: dict[str, Any] | None = None
        if should_track:
            request_payload = self._extract_payload(request)

        try:
            response = self.get_response(request)
        except Exception as exc:  # pragma: no cover - defensive logging
            if should_track:
                self._persist_log(
                    request=request,
                    status_code=getattr(exc, "status_code", 500),
                    request_payload=request_payload,
                    response_payload={"error": str(exc)},
                )
            raise

        if should_track:
            response_payload = self._extract_response_payload(response)
            self._persist_log(
                request=request,
                status_code=getattr(response, "status_code", 500),
                request_payload=request_payload,
                response_payload=response_payload,
            )

        return response

    def _extract_payload(self, request) -> dict[str, Any] | None:
        if not request.body:
            return None
        try:
            parsed = json.loads(request.body.decode("utf-8"))
            return self._mask_sensitive(parsed)
        except (json.JSONDecodeError, UnicodeDecodeError):  # pragma: no cover - non JSON
            return None

    def _extract_response_payload(self, response) -> dict[str, Any] | None:
        data = getattr(response, "data", None)
        if isinstance(data, dict):
            return self._mask_sensitive(data)
        return None

    def _mask_sensitive(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if payload is None:
            return None
        sensitive = getattr(settings, "AUDIT_LOG_SENSITIVE_FIELDS", set())
        masked = {}
        for key, value in payload.items():
            if key in sensitive:
                masked[key] = "***"
            else:
                try:
                    json.dumps(value)
                    masked[key] = value
                except TypeError:
                    masked[key] = str(value)
        return masked

    def _persist_log(
        self,
        *,
        request,
        status_code: int,
        request_payload: dict[str, Any] | None,
        response_payload: dict[str, Any] | None,
    ) -> None:
        tenant = getattr(request, "tenant", None)
        user = request.user if request.user.is_authenticated else None
        action = getattr(request, "audit_action", None) or f"{request.method} {request.path}"
        AuditLog.objects.create(
            tenant=tenant if getattr(tenant, "pk", None) else None,
            user=user,
            action=action,
            path=request.path,
            method=request.method,
            status_code=status_code,
            request_payload=request_payload or {},
            response_payload=response_payload or {},
            ip_address=self._get_ip(request),
        )
        self.logger.info(
            "%s %s %s %s",
            action,
            request.method,
            request.path,
            status_code,
        )

    def _get_ip(self, request) -> str | None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

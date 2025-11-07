from __future__ import annotations

from django.db import connection
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import Membership, Tenant, User
from ..tenant import activate_tenant


class TenancyIsolationTests(APITestCase):
    def setUp(self):
        self.signin_url = reverse("api:sign-in")
        self.current_tenant_url = reverse("api:current-tenant")
        self.tenant_a = Tenant.objects.create(name="Alpha Retail", slug="alpha-retail")
        self.tenant_a.ensure_system_roles()
        self.tenant_b = Tenant.objects.create(name="Beta Retail", slug="beta-retail")
        self.tenant_b.ensure_system_roles()

        self.user_a = User.objects.create_user(
            email="alpha@example.com", password="StrongPass123", full_name="Alpha Admin"
        )
        self.user_b = User.objects.create_user(
            email="beta@example.com", password="StrongPass123", full_name="Beta Admin"
        )

        with activate_tenant(self.tenant_a):
            Membership.objects.create(
                tenant=self.tenant_a,
                user=self.user_a,
                role=self.tenant_a.roles.get(slug="owner"),
                status=Membership.Status.ACTIVE,
            )
        with activate_tenant(self.tenant_b):
            Membership.objects.create(
                tenant=self.tenant_b,
                user=self.user_b,
                role=self.tenant_b.roles.get(slug="owner"),
                status=Membership.Status.ACTIVE,
            )

    def _access_token(self, email: str, password: str, tenant_slug: str) -> str:
        response = self.client.post(
            self.signin_url,
            data={"email": email, "password": password, "tenantSlug": tenant_slug},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data["accessToken"]

    def test_rls_blocks_cross_tenant_reads(self):
        if connection.vendor != "postgresql":
            self.skipTest("Row-level security policies require PostgreSQL")
        with activate_tenant(self.tenant_a):
            self.assertEqual(Membership.objects.count(), 1)
            self.assertTrue(
                Membership.objects.filter(tenant=self.tenant_a, user=self.user_a).exists()
            )
            self.assertFalse(
                Membership.objects.filter(tenant=self.tenant_b, user=self.user_b).exists()
            )

        with activate_tenant(self.tenant_b):
            self.assertEqual(Membership.objects.count(), 1)

        with activate_tenant(None):
            self.assertEqual(Membership.objects.count(), 0)

    def test_current_tenant_endpoint_requires_header(self):
        token = self._access_token("alpha@example.com", "StrongPass123", self.tenant_a.slug)

        # Missing header should raise validation error
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.current_tenant_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # With header response includes tenant metadata
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT=self.tenant_a.slug
        )
        response = self.client.get(self.current_tenant_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tenantSlug"], self.tenant_a.slug)
        self.assertIn("timezone", response.data)
        self.assertIn("permissions", response.data)

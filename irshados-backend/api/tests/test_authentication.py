from __future__ import annotations

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import AuditLog, Invitation, Membership, Tenant, User
from ..tenant import activate_tenant


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse("api:sign-up")
        self.signin_url = reverse("api:sign-in")
        self.signout_url = reverse("api:sign-out")
        self.invite_create_url = reverse("api:invite-create")
        self.invite_accept_url = reverse("api:invite-accept")
        self.switch_tenant_url = reverse("api:switch-tenant")
        self.refresh_url = reverse("api:token-refresh")

    def test_user_can_register_with_new_tenant(self):
        payload = {
            "userName": "Irshad Admin",
            "email": "owner@example.com",
            "password": "SecurePass123",
            "tenantMode": "new",
            "tenantName": "Irshad HQ",
        }
        response = self.client.post(self.signup_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("accessToken", response.data)
        self.assertIn("refreshToken", response.data)

        user = User.objects.get(email="owner@example.com")
        tenant = Tenant.objects.get(name="Irshad HQ")
        with activate_tenant(tenant):
            membership = Membership.objects.get(user=user, tenant=tenant)
        self.assertEqual(membership.role.slug, "owner")

    def test_existing_user_can_join_existing_tenant(self):
        tenant = Tenant.objects.create(name="Retail One", slug="retail-one")
        tenant.ensure_system_roles()
        user = User.objects.create_user(
            email="consultant@example.com",
            password="SecurePass123",
            full_name="Retail Consultant",
        )

        payload = {
            "userName": "Retail Consultant",
            "email": "consultant@example.com",
            "password": "SecurePass123",
            "tenantMode": "existing",
            "tenantSlug": tenant.slug,
            "roleSlug": "admin",
        }

        response = self.client.post(self.signup_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("accessToken", response.data)
        with activate_tenant(tenant):
            membership = Membership.objects.get(tenant=tenant, user=user)
        self.assertEqual(membership.role.slug, "staff")

    def test_sign_in_requires_membership(self):
        tenant = Tenant.objects.create(name="Retail One", slug="retail-one")
        tenant.ensure_system_roles()
        other_tenant = Tenant.objects.create(name="Retail Two", slug="retail-two")
        other_tenant.ensure_system_roles()
        user = User.objects.create_user(
            email="member@example.com",
            password="SecurePass123",
            full_name="Member",
        )
        with activate_tenant(tenant):
            Membership.objects.create(
                tenant=tenant,
                user=user,
                role=tenant.roles.get(slug="staff"),
                status=Membership.Status.ACTIVE,
            )

        payload = {
            "email": "member@example.com",
            "password": "SecurePass123",
            "tenantSlug": other_tenant.slug,
        }
        response = self.client.post(self.signin_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tenantSlug", response.data)

    def test_invitation_flow_enforces_rbac_and_creates_audit_logs(self):
        tenant = Tenant.objects.create(name="Retail One", slug="retail-one")
        tenant.ensure_system_roles()
        staff = User.objects.create_user(
            email="staff@example.com",
            password="SecurePass123",
            full_name="Retail Staff",
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="SecurePass123",
            full_name="Retail Owner",
        )
        with activate_tenant(tenant):
            Membership.objects.create(
                tenant=tenant,
                user=staff,
                role=tenant.roles.get(slug="staff"),
                status=Membership.Status.ACTIVE,
            )
            Membership.objects.create(
                tenant=tenant,
                user=owner,
                role=tenant.roles.get(slug="owner"),
                status=Membership.Status.ACTIVE,
            )

        sign_in_staff = self.client.post(
            self.signin_url,
            data={
                "email": "staff@example.com",
                "password": "SecurePass123",
                "tenantSlug": tenant.slug,
            },
            format="json",
        )
        self.assertEqual(sign_in_staff.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {sign_in_staff.data['accessToken']}",
            HTTP_X_TENANT=tenant.slug,
        )
        forbidden = self.client.post(
            self.invite_create_url,
            data={"email": "invitee@example.com"},
            format="json",
        )
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials()  # clear staff credentials
        sign_in_owner = self.client.post(
            self.signin_url,
            data={
                "email": "owner@example.com",
                "password": "SecurePass123",
                "tenantSlug": tenant.slug,
            },
            format="json",
        )
        self.assertEqual(sign_in_owner.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {sign_in_owner.data['accessToken']}",
            HTTP_X_TENANT=tenant.slug,
        )
        create_invite = self.client.post(
            self.invite_create_url,
            data={"email": "invitee@example.com", "roleSlug": "staff"},
            format="json",
        )
        self.assertEqual(create_invite.status_code, status.HTTP_201_CREATED)
        invitation_id = create_invite.data["id"]
        invitation = Invitation.objects.get(id=invitation_id)

        accept_response = self.client.post(
            self.invite_accept_url,
            data={
                "token": invitation.token,
                "email": "invitee@example.com",
                "password": "SecurePass123",
            },
            format="json",
        )
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Membership.objects.filter(
                tenant=tenant,
                user__email="invitee@example.com",
                status=Membership.Status.ACTIVE,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(action="auth.invite.accept").exists()
        )

    def test_tenant_switch_returns_new_tokens(self):
        tenant_one = Tenant.objects.create(name="Retail One", slug="retail-one")
        tenant_two = Tenant.objects.create(name="Retail Two", slug="retail-two")
        tenant_one.ensure_system_roles()
        tenant_two.ensure_system_roles()
        user = User.objects.create_user(
            email="member@example.com",
            password="SecurePass123",
            full_name="Member",
        )
        with activate_tenant(tenant_one):
            Membership.objects.create(
                tenant=tenant_one,
                user=user,
                role=tenant_one.roles.get(slug="staff"),
                status=Membership.Status.ACTIVE,
            )
        with activate_tenant(tenant_two):
            Membership.objects.create(
                tenant=tenant_two,
                user=user,
                role=tenant_two.roles.get(slug="admin"),
                status=Membership.Status.ACTIVE,
            )

        sign_in = self.client.post(
            self.signin_url,
            data={
                "email": "member@example.com",
                "password": "SecurePass123",
                "tenantSlug": tenant_one.slug,
            },
            format="json",
        )
        self.assertEqual(sign_in.status_code, status.HTTP_200_OK)
        original_access = sign_in.data["accessToken"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {original_access}")
        switch = self.client.post(
            self.switch_tenant_url,
            data={"tenantSlug": tenant_two.slug},
            format="json",
        )
        self.assertEqual(switch.status_code, status.HTTP_200_OK)
        self.assertNotEqual(original_access, switch.data["accessToken"])

    def test_refresh_rotates_tokens(self):
        signup = self.client.post(
            self.signup_url,
            data={
                "userName": "Refresh User",
                "email": "refresh@example.com",
                "password": "SecurePass123",
                "tenantMode": "new",
                "tenantName": "Refresh Co",
            },
            format="json",
        )
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        refresh_token = signup.data["refreshToken"]

        rotate = self.client.post(
            self.refresh_url,
            data={"refreshToken": refresh_token},
            format="json",
        )
        self.assertEqual(rotate.status_code, status.HTTP_200_OK)
        self.assertIn("accessToken", rotate.data)
        self.assertIn("refreshToken", rotate.data)

        reuse = self.client.post(
            self.refresh_url,
            data={"refreshToken": refresh_token},
            format="json",
        )
        self.assertEqual(reuse.status_code, status.HTTP_400_BAD_REQUEST)

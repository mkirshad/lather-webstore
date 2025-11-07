from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ...models import Membership, Tenant, ensure_permission_catalogue
from ...tenant import activate_tenant

User = get_user_model()


class Command(BaseCommand):
    help = "Create development tenants, roles, and seed users."

    def handle(self, *args, **options):
        ensure_permission_catalogue()

        tenants = [
            {
                "name": "ECME Demo Retail",
                "slug": "ecme-demo-retail",
                "timezone": "Asia/Karachi",
                "branding": {"primaryColor": "#1E3A8A", "accentColor": "#F97316"},
                "settings": {"modules": {"pos": True, "restaurant": False}},
                "users": [
                    ("owner", "owner@demo.irshados.com", "Demo Owner"),
                    ("admin", "admin@demo.irshados.com", "Demo Admin"),
                    ("staff", "staff@demo.irshados.com", "Demo Staff"),
                ],
            },
            {
                "name": "Restaurant Pilot",
                "slug": "restaurant-pilot",
                "timezone": "Asia/Karachi",
                "branding": {"primaryColor": "#047857", "accentColor": "#F59E0B"},
                "settings": {"modules": {"pos": True, "restaurant": True}},
                "users": [
                    ("owner", "rest-owner@demo.irshados.com", "Pilot Owner"),
                    ("admin", "rest-admin@demo.irshados.com", "Pilot Admin"),
                    ("staff", "rest-staff@demo.irshados.com", "Pilot Staff"),
                ],
            },
        ]

        default_password = "ChangeMe123!"

        for data in tenants:
            tenant, _ = Tenant.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "timezone": data["timezone"],
                    "branding": data["branding"],
                    "settings": data["settings"],
                },
            )
            tenant.ensure_system_roles()
            self.stdout.write(self.style.SUCCESS(f"Tenant ready: {tenant.slug}"))

            with activate_tenant(tenant):
                for role_slug, email, full_name in data["users"]:
                    user, _ = User.objects.get_or_create(
                        email=email,
                        defaults={"full_name": full_name},
                    )
                    if user.full_name != full_name:
                        user.full_name = full_name
                        user.save(update_fields=["full_name"])
                    if not user.has_usable_password():
                        user.set_password(default_password)
                        user.save(update_fields=["password"])
                    role = tenant.roles.get(slug=role_slug)
                    membership, created = Membership.objects.get_or_create(
                        tenant=tenant,
                        user=user,
                        defaults={"role": role, "status": Membership.Status.ACTIVE},
                    )
                    if not created and membership.role_id != role.id:
                        membership.role = role
                        membership.status = Membership.Status.ACTIVE
                        membership.save(update_fields=["role", "status"])
                    self.stdout.write(
                        f"  ↳ {email} mapped to {tenant.slug} as {role.slug}"
                    )

        self.stdout.write(self.style.SUCCESS("Development tenants bootstrapped."))

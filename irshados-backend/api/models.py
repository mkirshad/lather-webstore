from __future__ import annotations

import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .tenant import activate_tenant

DEFAULT_PERMISSION_CATALOGUE: dict[str, dict[str, str]] = {
    "tenant.manage": {
        "name": "Manage Tenant",
        "description": "Administer tenant configuration, billing, and lifecycle settings.",
    },
    "restaurant.view": {
        "name": "View Restaurant",
        "description": "View restaurant menus, tickets, and kitchen dashboards.",
    },
    "restaurant.manage": {
        "name": "Manage Restaurant",
        "description": "Manage restaurant menus, recipes, and kitchen operations.",
    },
    "inventory.view": {
        "name": "View Inventory",
        "description": "Read-only access to inventory, stock movements, and warehouse balances inspired by Fishbowl inventory snapshots.",
    },
    "inventory.manage": {
        "name": "Manage Inventory",
        "description": "Create and adjust stock transactions paralleling Fishbowl move/adjust workflows.",
    },
    "inventory.report": {
        "name": "Inventory Reporting",
        "description": "Access inventory balancing, costing, and ledger exports.",
    },
    "purchasing.view": {
        "name": "View Purchasing",
        "description": "Read-only access to purchase pipelines, suppliers, and bills.",
    },
    "purchasing.manage": {
        "name": "Manage Purchasing",
        "description": "Oversee purchase orders and goods receipts similar to Fishbowl PO to GRN flows.",
    },
    "sales.view": {
        "name": "View Sales",
        "description": "Read-only access to sales orders, customers, and invoices.",
    },
    "sales.manage": {
        "name": "Manage Sales",
        "description": "Manage sales orders, deliveries, and invoicing for tenant operations.",
    },
    "pos.view": {
        "name": "View POS",
        "description": "Review POS shift history and register journals.",
    },
    "pos.manage": {
        "name": "Manage POS",
        "description": "Create POS shifts, reconcile drawers, and process real-time or offline transactions.",
    },
    "reports.view": {
        "name": "View Reports",
        "description": "Access consolidated reporting dashboards and exports across modules.",
    },
}

DEFAULT_ROLE_PRESETS: dict[str, dict[str, object]] = {
    "owner": {
        "name": "Owner",
        "description": "Full control of tenant settings and operational modules.",
        "permissions": list(DEFAULT_PERMISSION_CATALOGUE.keys()),
    },
    "admin": {
        "name": "Administrator",
        "description": "Day-to-day administration across inventory, purchasing, and sales.",
        "permissions": [
            "inventory.manage",
            "inventory.report",
            "inventory.view",
            "purchasing.manage",
            "purchasing.view",
            "sales.manage",
            "sales.view",
            "pos.manage",
            "pos.view",
            "reports.view",
            "restaurant.manage",
            "restaurant.view",
        ],
    },
    "staff": {
        "name": "Staff",
        "description": "Operational access for frontline staff with read-only tenant management.",
        "permissions": [
            "inventory.view",
            "sales.manage",
            "sales.view",
            "pos.manage",
            "pos.view",
            "restaurant.view",
        ],
    },
}


def ensure_permission_catalogue() -> None:
    for code, meta in DEFAULT_PERMISSION_CATALOGUE.items():
        Permission.objects.get_or_create(
            code=code,
            defaults={
                "name": meta["name"],
                "description": meta["description"],
            },
        )


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    domain = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    branding = models.JSONField(default=dict, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def ensure_slug(self):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            index = 1
            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{index}"
                index += 1
            self.slug = slug

    def save(self, *args, **kwargs):
        self.ensure_slug()
        super().save(*args, **kwargs)

    def ensure_system_roles(self) -> None:
        ensure_permission_catalogue()
        with activate_tenant(self):
            for slug, preset in DEFAULT_ROLE_PRESETS.items():
                role, _ = self.roles.get_or_create(
                    slug=slug,
                    defaults={
                        "name": preset["name"],
                        "description": preset["description"],
                        "is_system": True,
                    },
                )
                desired_codes: list[str] = list(preset["permissions"])
                for code in desired_codes:
                    permission = Permission.objects.get(code=code)
                    RolePermission.objects.get_or_create(role=role, permission=permission)
                RolePermission.objects.filter(role=role).exclude(
                    permission__code__in=desired_codes
                ).delete()


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        related_name="roles",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)
    permissions = models.ManyToManyField(
        Permission,
        through="RolePermission",
        related_name="roles",
        blank=True,
    )

    class Meta:
        unique_together = (("tenant", "slug"), ("tenant", "name"))
        ordering = ["tenant__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.slug})"


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        related_name="role_permissions",
        on_delete=models.CASCADE,
    )
    permission = models.ForeignKey(
        Permission,
        related_name="permission_roles",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self) -> str:
        return f"{self.role} → {self.permission.code}"


class Membership(models.Model):
    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        Role,
        related_name="memberships",
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "user")
        ordering = ["tenant__name", "user__full_name"]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.tenant.slug} ({self.role.slug})"

    @property
    def authority(self) -> list[str]:
        return [self.role.slug]

    @property
    def permission_codes(self) -> list[str]:
        return list(self.role.permissions.values_list("code", flat=True))

    def activate(self) -> None:
        self.status = Membership.Status.ACTIVE
        self.save(update_fields=["status"])


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REVOKED = "revoked", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        related_name="invitations",
        on_delete=models.CASCADE,
    )
    email = models.EmailField()
    full_name = models.CharField(max_length=255, blank=True)
    role = models.ForeignKey(
        Role,
        related_name="invitations",
        on_delete=models.PROTECT,
    )
    token = models.CharField(max_length=128, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["email", "status"]),
        ]

    def __str__(self) -> str:
        return f"Invite {self.email} → {self.tenant.slug}"

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    def mark_accepted(self) -> None:
        self.status = Invitation.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=["status", "accepted_at"])

    def revoke(self) -> None:
        self.status = Invitation.Status.REVOKED
        self.save(update_fields=["status"])

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at


class TenantOwnedModel(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class UnitOfMeasure(TenantOwnedModel):
    class Category(models.TextChoices):
        QUANTITY = "quantity", "Quantity"
        WEIGHT = "weight", "Weight"
        VOLUME = "volume", "Volume"
        LENGTH = "length", "Length"
        TIME = "time", "Time"
        CUSTOM = "custom", "Custom"

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=12, blank=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.QUANTITY,
    )
    base_unit = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="derived_units",
    )
    conversion_factor = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        default=Decimal("1"),
    )
    is_decimal = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["tenant", "code"]),
        ]
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} ({self.name})"


class ProductCategory(TenantOwnedModel):
    code = models.CharField(max_length=48)
    name = models.CharField(max_length=160)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["tenant", "parent"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Tax(TenantOwnedModel):
    class Scope(models.TextChoices):
        SALES = "sales", "Sales"
        PURCHASE = "purchase", "Purchase"
        BOTH = "both", "Both"

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=120)
    rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0"))
    scope = models.CharField(
        max_length=12,
        choices=Scope.choices,
        default=Scope.BOTH,
    )
    is_inclusive = models.BooleanField(default=False)
    is_compound = models.BooleanField(default=False)
    account_code = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "code"]),
            models.Index(fields=["tenant", "scope"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.rate}%)"


class Product(TenantOwnedModel):
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    base_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="products_as_base",
    )
    default_tax = models.ForeignKey(
        Tax,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)
    attributes_schema = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["tenant", "category"]),
            models.Index(fields=["tenant", "is_active"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class ProductVariant(TenantOwnedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    sku = models.CharField(max_length=80)
    name = models.CharField(max_length=180)
    barcode = models.CharField(max_length=80, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    sales_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="variants_as_sales_uom",
    )
    conversion_factor = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        default=Decimal("1"),
    )
    cost_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
    )
    sales_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
    )
    is_active = models.BooleanField(default=True)
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=False)

    class Meta:
        unique_together = (("tenant", "sku"),)
        indexes = [
            models.Index(fields=["tenant", "sku"]),
            models.Index(fields=["tenant", "product"]),
            models.Index(fields=["tenant", "is_active"]),
        ]
        ordering = ("sku",)

    def __str__(self) -> str:
        return f"{self.sku}"


class PriceList(TenantOwnedModel):
    class Usage(models.TextChoices):
        SALES = "sales", "Sales"
        PURCHASE = "purchase", "Purchase"
        POS = "pos", "POS"

    code = models.CharField(max_length=48)
    name = models.CharField(max_length=180)
    currency = models.CharField(max_length=3, default="USD")
    usage = models.CharField(
        max_length=16,
        choices=Usage.choices,
        default=Usage.SALES,
    )
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "code"]),
            models.Index(fields=["tenant", "usage"]),
            models.Index(fields=["tenant", "is_default"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class PriceListItem(TenantOwnedModel):
    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="price_list_items",
    )
    min_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("1"),
    )
    price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )
    currency = models.CharField(max_length=3, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("tenant", "price_list", "variant", "min_quantity"),)
        indexes = [
            models.Index(fields=["tenant", "price_list"]),
            models.Index(fields=["tenant", "variant"]),
        ]
        ordering = ("price_list", "variant")

    def __str__(self) -> str:
        return f"{self.price_list.code}:{self.variant.sku}"


class Warehouse(TenantOwnedModel):
    code = models.CharField(max_length=48)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    contact_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "code"]),
            models.Index(fields=["tenant", "is_default"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class WarehouseBin(TenantOwnedModel):
    class BinType(models.TextChoices):
        STORAGE = "storage", "Storage"
        RECEIVING = "receiving", "Receiving"
        SHIPPING = "shipping", "Shipping"
        PICKING = "picking", "Picking"
        RETURNS = "returns", "Returns"

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="bins",
    )
    code = models.CharField(max_length=48)
    name = models.CharField(max_length=160)
    bin_type = models.CharField(
        max_length=16,
        choices=BinType.choices,
        default=BinType.STORAGE,
    )
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "warehouse", "code"),)
        indexes = [
            models.Index(fields=["tenant", "warehouse"]),
            models.Index(fields=["tenant", "bin_type"]),
        ]
        ordering = ("warehouse", "code")

    def __str__(self) -> str:
        return f"{self.warehouse.code}:{self.code}"


class Supplier(TenantOwnedModel):
    code = models.CharField(max_length=48)
    name = models.CharField(max_length=180)
    contact_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    mobile = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    tax_number = models.CharField(max_length=64, blank=True)
    payment_terms = models.CharField(max_length=120, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    billing_address = models.JSONField(default=dict, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "code"]),
            models.Index(fields=["tenant", "is_active"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Customer(TenantOwnedModel):
    code = models.CharField(max_length=48)
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    mobile = models.CharField(max_length=32, blank=True)
    website = models.URLField(blank=True)
    tax_number = models.CharField(max_length=64, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    credit_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
    )
    billing_address = models.JSONField(default=dict, blank=True)
    shipping_address = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "code"),)
        indexes = [
            models.Index(fields=["tenant", "code"]),
            models.Index(fields=["tenant", "is_active"]),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class InventoryBalance(TenantOwnedModel):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory_balances",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="inventory_balances",
    )
    on_hand = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    allocated = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    on_order = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    average_cost = models.DecimalField(max_digits=16, decimal_places=6, default=Decimal("0"))
    last_movement_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("tenant", "variant", "warehouse"),)
        indexes = [
            models.Index(fields=["tenant", "variant"]),
            models.Index(fields=["tenant", "warehouse"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku}@{self.warehouse.code}"


class StockMovement(TenantOwnedModel):
    class MovementType(models.TextChoices):
        PURCHASE_RECEIPT = "purchase_receipt", "Purchase Receipt"
        PURCHASE_RETURN = "purchase_return", "Purchase Return"
        SALE_SHIPMENT = "sale_shipment", "Sales Shipment"
        SALE_RETURN = "sale_return", "Sales Return"
        ADJUSTMENT = "adjustment", "Adjustment"
        TRANSFER_OUT = "transfer_out", "Transfer Out"
        TRANSFER_IN = "transfer_in", "Transfer In"
        POS_SALE = "pos_sale", "POS Sale"
        POS_RETURN = "pos_return", "POS Return"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        VOID = "void", "Void"

    movement_type = models.CharField(max_length=32, choices=MovementType.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.POSTED,
    )
    reference_number = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_movements",
    )
    performed_at = models.DateTimeField(default=timezone.now)
    source_document_type = models.CharField(max_length=64, blank=True)
    source_document_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "movement_type"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "performed_at"]),
        ]
        ordering = ("-performed_at", "-created_at")

    def __str__(self) -> str:
        return f"{self.movement_type}:{self.reference_number or self.id}"


class StockMovementLine(TenantOwnedModel):
    movement = models.ForeignKey(
        StockMovement,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="stock_movement_lines",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_movement_lines",
    )
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=16, decimal_places=6)
    value_delta = models.DecimalField(max_digits=18, decimal_places=6)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "movement"]),
            models.Index(fields=["tenant", "variant"]),
            models.Index(fields=["tenant", "warehouse"]),
        ]

    def __str__(self) -> str:
        direction = "in" if self.quantity >= 0 else "out"
        return f"{self.variant.sku} {direction} {abs(self.quantity)}"


class InventoryLedgerEntry(TenantOwnedModel):
    movement = models.ForeignKey(
        StockMovement,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )
    line = models.ForeignKey(
        StockMovementLine,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )
    quantity_delta = models.DecimalField(max_digits=16, decimal_places=3)
    value_delta = models.DecimalField(max_digits=18, decimal_places=6)
    running_quantity = models.DecimalField(max_digits=16, decimal_places=3)
    running_value = models.DecimalField(max_digits=18, decimal_places=6)
    average_cost = models.DecimalField(max_digits=16, decimal_places=6)
    reference_type = models.CharField(max_length=64, blank=True)
    reference_id = models.CharField(max_length=64, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "variant"]),
            models.Index(fields=["tenant", "warehouse"]),
            models.Index(fields=["tenant", "created_at"]),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.variant.sku} Δ{self.quantity_delta}"


class PurchaseOrder(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        RECEIVING = "receiving", "Receiving"
        RECEIVED = "received", "Received"
        BILLED = "billed", "Billed"
        PAID = "paid", "Paid"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(max_length=48)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    subtotal = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_purchase_orders",
    )

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "supplier"]),
            models.Index(fields=["tenant", "order_date"]),
        ]
        ordering = ("-order_date", "-created_at")

    def __str__(self) -> str:
        return f"PO {self.number}"


class PurchaseOrderLine(TenantOwnedModel):
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )
    description = models.TextField(blank=True)
    ordered_quantity = models.DecimalField(max_digits=16, decimal_places=3)
    received_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    billed_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "order"]),
            models.Index(fields=["tenant", "variant"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} x {self.ordered_quantity}"


class PurchaseReceipt(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="receipts",
    )
    number = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    receipt_date = models.DateField(default=timezone.now)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchase_receipts",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="purchase_receipts",
    )
    stock_movement = models.ForeignKey(
        StockMovement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchase_receipts",
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "receipt_date"]),
        ]
        ordering = ("-receipt_date", "-created_at")

    def __str__(self) -> str:
        return f"GRN {self.number}"


class PurchaseReceiptLine(TenantOwnedModel):
    receipt = models.ForeignKey(
        PurchaseReceipt,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    order_line = models.ForeignKey(
        PurchaseOrderLine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receipt_lines",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="purchase_receipt_lines",
    )
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "receipt"]),
            models.Index(fields=["tenant", "variant"]),
        ]


class PurchaseBill(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="bills",
    )
    number = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    bill_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    subtotal = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "bill_date"]),
        ]
        ordering = ("-bill_date", "-created_at")

    def __str__(self) -> str:
        return f"Bill {self.number}"


class PurchaseBillLine(TenantOwnedModel):
    bill = models.ForeignKey(
        PurchaseBill,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    order_line = models.ForeignKey(
        PurchaseOrderLine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bill_lines",
    )
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "bill"]),
        ]


class PurchasePayment(TenantOwnedModel):
    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        VOID = "void", "Void"

    bill = models.ForeignKey(
        PurchaseBill,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    number = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.POSTED,
    )
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    method = models.CharField(max_length=48, blank=True)
    reference = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "payment_date"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return f"Payment {self.number}"


class SalesOrder(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        PICKING = "picking", "Picking"
        FULFILLED = "fulfilled", "Fulfilled"
        INVOICED = "invoiced", "Invoiced"
        PAID = "paid", "Paid"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(max_length=48)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="sales_orders",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    order_date = models.DateField(default=timezone.now)
    ship_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    subtotal = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_sales_orders",
    )

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "customer"]),
            models.Index(fields=["tenant", "order_date"]),
        ]
        ordering = ("-order_date", "-created_at")

    def __str__(self) -> str:
        return f"SO {self.number}"


class SalesOrderLine(TenantOwnedModel):
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="sales_order_lines",
    )
    description = models.TextField(blank=True)
    ordered_quantity = models.DecimalField(max_digits=16, decimal_places=3)
    delivered_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    invoiced_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "order"]),
            models.Index(fields=["tenant", "variant"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} x {self.ordered_quantity}"


class DeliveryNote(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    number = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    delivery_date = models.DateField(default=timezone.now)
    fulfilled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="delivery_notes",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="delivery_notes",
    )
    stock_movement = models.ForeignKey(
        StockMovement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="delivery_notes",
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "delivery_date"]),
        ]
        ordering = ("-delivery_date", "-created_at")

    def __str__(self) -> str:
        return f"DN {self.number}"


class DeliveryNoteLine(TenantOwnedModel):
    delivery = models.ForeignKey(
        DeliveryNote,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    order_line = models.ForeignKey(
        SalesOrderLine,
        on_delete=models.SET_NULL,
        related_name="delivery_lines",
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="delivery_lines",
    )
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "delivery"]),
            models.Index(fields=["tenant", "variant"]),
        ]


class SalesInvoice(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    number = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    subtotal = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "invoice_date"]),
        ]
        ordering = ("-invoice_date", "-created_at")

    def __str__(self) -> str:
        return f"Invoice {self.number}"


class SalesInvoiceLine(TenantOwnedModel):
    invoice = models.ForeignKey(
        SalesInvoice,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    order_line = models.ForeignKey(
        SalesOrderLine,
        on_delete=models.SET_NULL,
        related_name="invoice_lines",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "invoice"]),
        ]


class SalesPayment(TenantOwnedModel):
    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        VOID = "void", "Void"

    invoice = models.ForeignKey(
        SalesInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    number = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.POSTED,
    )
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    method = models.CharField(max_length=48, blank=True)
    reference = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "payment_date"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return f"SalesPayment {self.number}"


class SalesRefund(TenantOwnedModel):
    invoice = models.ForeignKey(
        SalesInvoice,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    number = models.CharField(max_length=48)
    refund_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "refund_date"]),
        ]

    def __str__(self) -> str:
        return f"Refund {self.number}"


class Menu(TenantOwnedModel):
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "name"),)
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class MenuSection(TenantOwnedModel):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=160)
    sort_order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = (("tenant", "menu", "name"),)
        ordering = ("menu", "sort_order", "name")

    def __str__(self) -> str:
        return f"{self.menu.name} • {self.name}"


class MenuItem(TenantOwnedModel):
    section = models.ForeignKey(
        MenuSection,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=48, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    preparation_time_seconds = models.PositiveIntegerField(default=0)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_items",
    )
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = (("tenant", "section", "name"),)
        ordering = ("section", "name")

    def __str__(self) -> str:
        return self.name


class MenuModifierGroup(TenantOwnedModel):
    item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="modifier_groups",
    )
    name = models.CharField(max_length=140)
    is_required = models.BooleanField(default=False)
    min_required = models.PositiveIntegerField(default=0)
    max_allowed = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("tenant", "item", "name"),)
        ordering = ("item", "sort_order", "name")

    def __str__(self) -> str:
        return f"{self.item.name} • {self.name}"


class MenuModifierOption(TenantOwnedModel):
    group = models.ForeignKey(
        MenuModifierGroup,
        on_delete=models.CASCADE,
        related_name="options",
    )
    name = models.CharField(max_length=140)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    variant = models.ForeignKey(
        ProductVariant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="modifier_options",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("tenant", "group", "name"),)
        ordering = ("group", "sort_order", "name")

    def __str__(self) -> str:
        return f"{self.group.name} • {self.name}"


class Recipe(TenantOwnedModel):
    item = models.OneToOneField(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="recipe",
    )
    instructions = models.TextField(blank=True)
    yield_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    yield_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipes",
    )

    class Meta:
        ordering = ("item",)

    def __str__(self) -> str:
        return f"Recipe for {self.item.name}"


class RecipeComponent(TenantOwnedModel):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="components",
    )
    ingredient = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="recipe_components",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="recipe_components",
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("tenant", "recipe", "ingredient"),)
        ordering = ("recipe", "ingredient")

    def __str__(self) -> str:
        return f"{self.ingredient.sku} x {self.quantity}"


class KitchenOrderTicket(TenantOwnedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        READY = "ready", "Ready"
        SERVED = "served", "Served"
        CANCELLED = "cancelled", "Cancelled"

    class Source(models.TextChoices):
        DINE_IN = "dine_in", "Dine In"
        TAKEAWAY = "takeaway", "Takeaway"
        DELIVERY = "delivery", "Delivery"
        QR = "qr", "QR"

    ticket_number = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.DINE_IN)
    table_number = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)
    placed_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("tenant", "ticket_number"),)
        ordering = ("-placed_at", "-created_at")

    def __str__(self) -> str:
        return f"KOT {self.ticket_number}"

    def mark_ready(self) -> None:
        self.status = KitchenOrderTicket.Status.READY
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def mark_served(self) -> None:
        self.status = KitchenOrderTicket.Status.SERVED
        self.save(update_fields=["status", "updated_at"])

    def cancel(self) -> None:
        self.status = KitchenOrderTicket.Status.CANCELLED
        self.save(update_fields=["status", "updated_at"])


class KitchenOrderLine(TenantOwnedModel):
    ticket = models.ForeignKey(
        KitchenOrderTicket,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="ticket_lines",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1"))
    modifiers = models.JSONField(default=list, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("ticket", "id")

    def __str__(self) -> str:
        return f"{self.item.name} x {self.quantity}"


class KitchenDisplayEvent(TenantOwnedModel):
    class Action(models.TextChoices):
        BUMP = "bump", "Bump"
        RECALL = "recall", "Recall"

    ticket = models.ForeignKey(
        KitchenOrderTicket,
        on_delete=models.CASCADE,
        related_name="kds_events",
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    actor = models.CharField(max_length=120, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-occurred_at",)

    def __str__(self) -> str:
        return f"{self.ticket.ticket_number} {self.action}"


class QROrderingToken(TenantOwnedModel):
    token = models.CharField(max_length=64, unique=True)
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="qr_tokens",
    )
    table_number = models.CharField(max_length=32, blank=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "menu"]),
            models.Index(fields=["tenant", "table_number"]),
        ]
        ordering = ("-expires_at",)

    def __str__(self) -> str:
        return f"QR {self.token}"


class POSShift(TenantOwnedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    register_code = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="pos_shifts_opened",
        on_delete=models.SET_NULL,
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="pos_shifts_closed",
        on_delete=models.SET_NULL,
    )
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    closing_float = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "register_code"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "opened_at"]),
        ]
        ordering = ("-opened_at",)

    def __str__(self) -> str:
        return f"Shift {self.register_code} {self.opened_at:%Y-%m-%d}"


class POSSale(TenantOwnedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"
        VOID = "void", "Void"

    shift = models.ForeignKey(
        POSShift,
        on_delete=models.CASCADE,
        related_name="sales",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="pos_sales",
    )
    reference = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        related_name="pos_sales",
        on_delete=models.SET_NULL,
    )
    subtotal = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    paid_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    change_due = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    stock_movement = models.ForeignKey(
        StockMovement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pos_sales",
    )
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "reference"),)
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "shift"]),
            models.Index(fields=["tenant", "warehouse"]),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"POS Sale {self.reference}"


class POSSaleItem(TenantOwnedModel):
    sale = models.ForeignKey(
        POSSale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="pos_sale_items",
    )
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4)
    discount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "sale"]),
            models.Index(fields=["tenant", "variant"]),
        ]


class POSSalePayment(TenantOwnedModel):
    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        VOID = "void", "Void"

    sale = models.ForeignKey(
        POSSale,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    method = models.CharField(max_length=32)
    amount = models.DecimalField(max_digits=16, decimal_places=4)
    received_at = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.POSTED,
    )

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "sale"]),
            models.Index(fields=["tenant", "method"]),
            models.Index(fields=["tenant", "status"]),
        ]


class POSReceipt(TenantOwnedModel):
    sale = models.OneToOneField(
        POSSale,
        on_delete=models.CASCADE,
        related_name="receipt",
    )
    number = models.CharField(max_length=64)
    rendered_payload = models.JSONField(default=dict, blank=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("tenant", "number"),)
        indexes = [
            models.Index(fields=["tenant", "number"]),
        ]


class POSOfflineQueueItem(TenantOwnedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCED = "synced", "Synced"
        FAILED = "failed", "Failed"

    operation = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.CharField(max_length=255, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "operation"]),
        ]


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField()
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} ({self.status_code})"


class BlacklistedToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    jti = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"blacklist:{self.jti}"

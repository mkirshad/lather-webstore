from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Tuple

from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from .models import (
    Customer,
    Invitation,
    Membership,
    PriceList,
    PriceListItem,
    Product,
    ProductCategory,
    ProductVariant,
    Role,
    Supplier,
    Tax,
    Tenant,
    UnitOfMeasure,
    User,
    Warehouse,
    WarehouseBin,
    InventoryBalance,
    StockMovement,
    StockMovementLine,
    InventoryLedgerEntry,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
    PurchaseBill,
    PurchaseBillLine,
    PurchasePayment,
    SalesInvoice,
    SalesInvoiceLine,
    SalesOrder,
    SalesOrderLine,
    SalesPayment,
    SalesRefund,
    DeliveryNote,
    DeliveryNoteLine,
    POSShift,
    POSSale,
    POSSaleItem,
    POSSalePayment,
    POSReceipt,
    POSOfflineQueueItem,
    Menu,
    MenuSection,
    MenuItem,
    MenuModifierGroup,
    MenuModifierOption,
    Recipe,
    RecipeComponent,
    KitchenOrderTicket,
    KitchenOrderLine,
    KitchenDisplayEvent,
    QROrderingToken,
)
from .services.inventory import (
    DECIMAL_PRECISION_CURRENCY,
    InventoryService,
    StockMovementLineParams,
)
from .services.purchasing import PurchasingService
from .services.sales import SalesService
from .services.pos import POSService
from .tasks import send_invitation_email
from .tenant import activate_tenant


logger = logging.getLogger("irshados.audit")


def _normalize_slug(slug: str) -> str:
    normalized = slugify(slug)
    return normalized


class TenantSummarySerializer(serializers.Serializer):
    tenantId = serializers.UUIDField(source="tenant.id")
    tenantSlug = serializers.CharField(source="tenant.slug")
    tenantName = serializers.CharField(source="tenant.name")
    role = serializers.CharField(source="role.slug")
    permissions = serializers.ListField(
        child=serializers.CharField(), source="permission_codes"
    )


class UserSerializer(serializers.ModelSerializer):
    tenants = serializers.SerializerMethodField()
    activeTenant = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "tenants",
            "activeTenant",
        ]

    def get_tenants(self, obj: User):
        memberships = (
            obj.memberships.select_related("tenant", "role")
            .filter(status=Membership.Status.ACTIVE)
            .order_by("tenant__name")
        )
        return [
            {
                "tenantId": membership.tenant_id,
                "tenantSlug": membership.tenant.slug,
                "tenantName": membership.tenant.name,
                "role": membership.role.slug,
                "permissions": membership.permission_codes,
            }
            for membership in memberships
        ]

    def get_activeTenant(self, obj: User):
        membership = self.context.get("active_membership")
        if not membership:
            return None
        return {
            "tenantId": membership.tenant_id,
            "tenantSlug": membership.tenant.slug,
            "tenantName": membership.tenant.name,
            "role": membership.role.slug,
            "permissions": membership.permission_codes,
        }


class SignUpSerializer(serializers.Serializer):
    userName = serializers.CharField(
        source="full_name",
        max_length=255,
        required=False,
        allow_blank=True,
    )
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    tenantMode = serializers.ChoiceField(
        choices=("existing", "new"),
        source="tenant_mode",
    )
    tenantSlug = serializers.CharField(
        source="tenant_slug",
        required=False,
        allow_blank=True,
    )
    tenantName = serializers.CharField(
        source="tenant_name",
        required=False,
        allow_blank=True,
        max_length=255,
    )
    tenantDomain = serializers.CharField(
        source="tenant_domain",
        required=False,
        allow_blank=True,
        max_length=255,
    )
    roleSlug = serializers.CharField(
        source="role_slug",
        required=False,
        allow_blank=True,
    )

    default_error_messages = {
        "invalid_credentials": "The password provided does not match the existing account.",
        "tenant_not_found": "We could not find a tenant with this slug.",
        "membership_exists": "You are already a member of this tenant.",
        "role_not_found": "The requested role does not exist for this tenant.",
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get("email")
        full_name = attrs.get("full_name")
        if not full_name and email:
            attrs["full_name"] = email

        tenant_mode = attrs.get("tenant_mode")
        tenant_slug = attrs.get("tenant_slug", "")
        tenant_name = attrs.get("tenant_name", "")

        if tenant_mode == "existing" and not tenant_slug:
            raise serializers.ValidationError(
                {"tenantSlug": "Provide the tenant slug you want to join."}
            )

        if tenant_mode == "new" and not tenant_name:
            raise serializers.ValidationError(
                {"tenantName": "Provide a name for the new tenant."}
            )

        return attrs

    def _get_or_create_user(self, email: str, password: str, full_name: str) -> Tuple[User, bool]:
        email = User.objects.normalize_email(email)
        user = User.objects.filter(email__iexact=email).first()
        if user:
            if not user.check_password(password):
                self.fail("invalid_credentials")
            if full_name and not user.full_name:
                user.full_name = full_name
                user.save(update_fields=["full_name"])
            return user, False
        user = User.objects.create_user(email=email, password=password, full_name=full_name)
        return user, True

    def _generate_unique_slug(self, base: str) -> str:
        base_slug = slugify(base) or "tenant"
        slug = base_slug
        index = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{index}"
            index += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data["full_name"]
        email = validated_data["email"]
        password = validated_data["password"]
        tenant_mode = validated_data["tenant_mode"]
        provided_slug = validated_data.get("tenant_slug", "")
        tenant_name = validated_data.get("tenant_name", "")
        tenant_domain = validated_data.get("tenant_domain", "")

        user, created = self._get_or_create_user(email, password, full_name)

        if tenant_mode == "existing":
            normalized_slug = _normalize_slug(provided_slug)
            try:
                tenant = Tenant.objects.get(slug__iexact=normalized_slug)
            except Tenant.DoesNotExist as exc:  # pragma: no cover - defensive
                raise serializers.ValidationError(
                    {"tenantSlug": self.error_messages["tenant_not_found"]}
                ) from exc
            tenant.ensure_system_roles()
            with activate_tenant(tenant):
                role = tenant.roles.get(slug="staff")
                membership, created_membership = Membership.objects.get_or_create(
                    tenant=tenant,
                    user=user,
                    defaults={"role": role, "status": Membership.Status.ACTIVE},
                )
        else:
            slug = provided_slug.strip() or self._generate_unique_slug(tenant_name)
            tenant = Tenant.objects.create(
                name=tenant_name,
                slug=_normalize_slug(slug),
                domain=tenant_domain,
            )
            tenant.ensure_system_roles()
            with activate_tenant(tenant):
                role = tenant.roles.get(slug="owner")
                membership = Membership.objects.create(
                    tenant=tenant,
                    user=user,
                    role=role,
                    status=Membership.Status.ACTIVE,
                )
            created_membership = True

        if not created_membership:
            self.fail("membership_exists")

        return {"user": user, "membership": membership}


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    tenantSlug = serializers.CharField(source="tenant_slug")

    default_error_messages = {
        "authorization_error": "Invalid email, password, or tenant.",
        "inactive": "This account is currently disabled.",
        "membership_missing": "You are not a member of the selected tenant.",
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs["email"]
        password = attrs["password"]
        tenant_slug = _normalize_slug(attrs["tenant_slug"])

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            self.fail("authorization_error")
        if not user.is_active:
            self.fail("inactive")

        try:
            tenant = Tenant.objects.get(slug__iexact=tenant_slug)
        except Tenant.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"tenantSlug": self.error_messages["membership_missing"]}
            ) from exc

        tenant.ensure_system_roles()
        with activate_tenant(tenant):
            try:
                membership = Membership.objects.select_related("tenant", "role").get(
                    tenant=tenant,
                    user=user,
                )
            except Membership.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"tenantSlug": self.error_messages["membership_missing"]}
                ) from exc

        if membership.status != Membership.Status.ACTIVE:
            self.fail("membership_missing")

        attrs["user"] = user
        attrs["membership"] = membership
        return attrs

    def create(self, validated_data):
        return {"user": validated_data["user"], "membership": validated_data["membership"]}


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    roleSlug = serializers.CharField(source="role_slug", required=False, allow_blank=True)
    fullName = serializers.CharField(source="full_name", required=False, allow_blank=True)
    expiresInDays = serializers.IntegerField(
        source="expires_in_days", default=7, min_value=1, max_value=90
    )

    default_error_messages = {
        "membership_exists": "The user is already a member of this tenant.",
    }

    def validate(self, attrs):
        tenant: Tenant = self.context["tenant"]
        tenant.ensure_system_roles()
        email = attrs["email"].lower()
        attrs["role_slug"] = slugify(attrs.get("role_slug") or "staff")

        existing_membership = Membership.objects.filter(
            tenant=tenant,
            user__email__iexact=email,
            status=Membership.Status.ACTIVE,
        ).exists()
        if existing_membership:
            self.fail("membership_exists")

        pending_invite = Invitation.objects.filter(
            tenant=tenant,
            email__iexact=email,
            status=Invitation.Status.PENDING,
        ).exists()
        if pending_invite:
            raise serializers.ValidationError(
                {"email": "An invitation has already been sent to this email."}
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        tenant: Tenant = self.context["tenant"]
        role_slug = validated_data.get("role_slug", "staff")
        role = tenant.roles.get(slug=role_slug)
        expires_at = timezone.now() + timedelta(days=validated_data["expires_in_days"])
        invitation = Invitation.objects.create(
            tenant=tenant,
            email=validated_data["email"],
            full_name=validated_data.get("full_name", ""),
            role=role,
            token=Invitation.generate_token(),
            invited_by=self.context.get("invited_by"),
            expires_at=expires_at,
        )
        try:
            send_invitation_email.delay(str(invitation.id))
        except Exception:  # pragma: no cover - broker failures
            logger.exception("Failed to enqueue invitation email for %s", invitation.email)
        return invitation


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    fullName = serializers.CharField(source="full_name", required=False, allow_blank=True)

    default_error_messages = {
        "invalid_token": "The invitation token is invalid or has already been used.",
        "expired": "The invitation has expired. Request a new invite from the administrator.",
        "email_mismatch": "This invitation was issued for a different email address.",
    }

    def validate(self, attrs):
        token = attrs["token"]
        try:
            invitation = Invitation.objects.select_related("tenant", "role").get(token=token)
        except Invitation.DoesNotExist:
            self.fail("invalid_token")

        if invitation.status != Invitation.Status.PENDING:
            self.fail("invalid_token")
        if invitation.is_expired:
            self.fail("expired")
        if invitation.email.lower() != attrs["email"].lower():
            self.fail("email_mismatch")

        attrs["invitation"] = invitation
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        invitation: Invitation = validated_data["invitation"]
        full_name = validated_data.get("full_name") or invitation.full_name
        email = validated_data["email"].lower()
        password = validated_data["password"]

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"full_name": full_name or email.split("@")[0]},
        )
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        user.set_password(password)
        user.is_active = True
        user.save()

        tenant = invitation.tenant
        tenant.ensure_system_roles()
        with activate_tenant(tenant):
            membership, _ = Membership.objects.update_or_create(
                tenant=tenant,
                user=user,
                defaults={
                    "role": invitation.role,
                    "status": Membership.Status.ACTIVE,
                },
            )

        invitation.mark_accepted()
        return {"user": user, "membership": membership}


class TenantSwitchSerializer(serializers.Serializer):
    tenantSlug = serializers.CharField(source="tenant_slug")

    default_error_messages = {
        "membership_missing": "You do not have access to the requested tenant.",
    }

    def validate(self, attrs):
        tenant_slug = _normalize_slug(attrs["tenant_slug"])
        user: User = self.context["user"]
        try:
            tenant = Tenant.objects.get(slug__iexact=tenant_slug)
        except Tenant.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"tenantSlug": self.error_messages["membership_missing"]}
            ) from exc

        tenant.ensure_system_roles()
        with activate_tenant(tenant):
            try:
                membership = Membership.objects.select_related("tenant", "role").get(
                    tenant=tenant,
                    user=user,
                    status=Membership.Status.ACTIVE,
                )
            except Membership.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"tenantSlug": self.error_messages["membership_missing"]}
                ) from exc

        attrs["membership"] = membership
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        return {
            "user": validated_data["user"],
            "membership": validated_data["membership"],
        }


class TenantOwnedSerializer(serializers.ModelSerializer):
    """Base serializer for tenant-scoped models."""

    read_only_fields = ("id", "created_at", "updated_at")

    def _get_tenant(self):
        tenant = self.context.get("tenant")
        if tenant is not None:
            return tenant
        request = self.context.get("request")
        if request is not None:
            return getattr(request, "tenant", None)
        return None

    def create(self, validated_data):
        tenant = self._get_tenant()
        if tenant is None and "tenant" not in validated_data:
            raise serializers.ValidationError({"detail": "Tenant context missing."})
        validated_data.setdefault("tenant", tenant)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("tenant", None)
        return super().update(instance, validated_data)

    class Meta:
        read_only_fields = ("id", "created_at", "updated_at")


class UnitOfMeasureSerializer(TenantOwnedSerializer):
    base_unit_name = serializers.CharField(source="base_unit.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = UnitOfMeasure
        fields = [
            "id",
            "code",
            "name",
            "symbol",
            "category",
            "base_unit",
            "base_unit_name",
            "conversion_factor",
            "is_decimal",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("base_unit_name",)

    def validate_base_unit(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or tenant.id != value.tenant_id:
            raise serializers.ValidationError("Base unit must belong to the current tenant.")
        if self.instance and self.instance.pk == value.pk:
            raise serializers.ValidationError("Base unit cannot reference the unit itself.")
        return value


class ProductCategorySerializer(TenantOwnedSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = ProductCategory
        fields = [
            "id",
            "code",
            "name",
            "parent",
            "parent_name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("parent_name",)

    def validate_parent(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or tenant.id != value.tenant_id:
            raise serializers.ValidationError("Parent category must belong to the current tenant.")
        if self.instance and self.instance.pk == value.pk:
            raise serializers.ValidationError("Category cannot be its own parent.")
        return value


class TaxSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = Tax
        fields = [
            "id",
            "code",
            "name",
            "rate",
            "scope",
            "is_inclusive",
            "is_compound",
            "account_code",
            "description",
            "metadata",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(TenantOwnedSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    base_uom_code = serializers.CharField(source="base_uom.code", read_only=True)
    default_tax_code = serializers.CharField(source="default_tax.code", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = Product
        fields = [
            "id",
            "code",
            "name",
            "description",
            "category",
            "category_name",
            "base_uom",
            "base_uom_code",
            "default_tax",
            "default_tax_code",
            "track_inventory",
            "allow_backorder",
            "attributes_schema",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "category_name",
            "base_uom_code",
            "default_tax_code",
        )

    def validate_category(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or tenant.id != value.tenant_id:
            raise serializers.ValidationError("Category must belong to the current tenant.")
        return value

    def validate_base_uom(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or tenant.id != value.tenant_id:
            raise serializers.ValidationError("Base unit must belong to the current tenant.")
        return value

    def validate_default_tax(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or tenant.id != value.tenant_id:
            raise serializers.ValidationError("Tax definition must belong to the current tenant.")
        return value


class ProductVariantSerializer(TenantOwnedSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sales_uom_code = serializers.CharField(source="sales_uom.code", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = ProductVariant
        fields = [
            "id",
            "product",
            "product_name",
            "sku",
            "name",
            "barcode",
            "attributes",
            "sales_uom",
            "sales_uom_code",
            "conversion_factor",
            "cost_price",
            "sales_price",
            "track_inventory",
            "allow_backorder",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "product_name",
            "sales_uom_code",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tenant = self._get_tenant()
        product = attrs.get("product") or getattr(self.instance, "product", None)
        sales_uom = attrs.get("sales_uom") or getattr(self.instance, "sales_uom", None)
        if tenant is None:
            raise serializers.ValidationError({"detail": "Tenant context missing."})
        if product and product.tenant_id != tenant.id:
            raise serializers.ValidationError({"product": "Product must belong to the current tenant."})
        if sales_uom and sales_uom.tenant_id != tenant.id:
            raise serializers.ValidationError({"sales_uom": "Sales unit must belong to the current tenant."})
        return attrs


class PriceListSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = PriceList
        fields = [
            "id",
            "code",
            "name",
            "currency",
            "usage",
            "description",
            "is_default",
            "is_active",
            "valid_from",
            "valid_to",
            "metadata",
            "created_at",
            "updated_at",
        ]


class PriceListItemSerializer(TenantOwnedSerializer):
    price_list_code = serializers.CharField(source="price_list.code", read_only=True)
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = PriceListItem
        fields = [
            "id",
            "price_list",
            "price_list_code",
            "variant",
            "variant_sku",
            "min_quantity",
            "price",
            "currency",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "price_list_code",
            "variant_sku",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tenant = self._get_tenant()
        price_list = attrs.get("price_list") or getattr(self.instance, "price_list", None)
        variant = attrs.get("variant") or getattr(self.instance, "variant", None)
        if tenant is None:
            raise serializers.ValidationError({"detail": "Tenant context missing."})
        if price_list and price_list.tenant_id != tenant.id:
            raise serializers.ValidationError({"price_list": "Price list must belong to the current tenant."})
        if variant and variant.tenant_id != tenant.id:
            raise serializers.ValidationError({"variant": "Variant must belong to the current tenant."})
        return attrs

    def create(self, validated_data):
        price_list = validated_data["price_list"]
        if not validated_data.get("currency"):
            validated_data["currency"] = price_list.currency
        validated_data["tenant"] = price_list.tenant
        return super().create(validated_data)

    def update(self, instance, validated_data):
        price_list = validated_data.get("price_list") or instance.price_list
        if price_list and not validated_data.get("currency"):
            validated_data["currency"] = price_list.currency
        return super().update(instance, validated_data)


class WarehouseSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = Warehouse
        fields = [
            "id",
            "code",
            "name",
            "description",
            "is_default",
            "contact_name",
            "phone",
            "email",
            "address",
            "metadata",
            "created_at",
            "updated_at",
        ]


class WarehouseBinSerializer(TenantOwnedSerializer):
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = WarehouseBin
        fields = [
            "id",
            "warehouse",
            "warehouse_code",
            "code",
            "name",
            "bin_type",
            "is_default",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("warehouse_code",)

    def validate_warehouse(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Warehouse must belong to the current tenant.")
        return value


class SupplierSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = Supplier
        fields = [
            "id",
            "code",
            "name",
            "contact_name",
            "email",
            "phone",
            "mobile",
            "website",
            "tax_number",
            "payment_terms",
            "currency",
            "billing_address",
            "shipping_address",
            "notes",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]


class CustomerSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = Customer
        fields = [
            "id",
            "code",
            "name",
            "email",
            "phone",
            "mobile",
            "website",
            "tax_number",
            "currency",
            "credit_limit",
            "balance",
            "billing_address",
            "shipping_address",
            "notes",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]


class InventoryBalanceSerializer(TenantOwnedSerializer):
    variant_id = serializers.UUIDField(source="variant.id", read_only=True)
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = InventoryBalance
        fields = [
            "id",
            "variant",
            "variant_id",
            "variant_sku",
            "variant_name",
            "warehouse",
            "warehouse_code",
            "warehouse_name",
            "on_hand",
            "allocated",
            "on_order",
            "average_cost",
            "last_movement_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "variant_id",
            "variant_sku",
            "variant_name",
            "warehouse_code",
            "warehouse_name",
        )


class StockMovementLineReadSerializer(serializers.ModelSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)

    class Meta:
        model = StockMovementLine
        fields = [
            "id",
            "variant",
            "variant_sku",
            "warehouse",
            "warehouse_code",
            "quantity",
            "unit_cost",
            "value_delta",
            "metadata",
        ]
        read_only_fields = fields


class StockMovementLineWriteSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
    quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=16, decimal_places=6, required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)
    reference_type = serializers.CharField(required=False, allow_blank=True, default="")
    reference_id = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")


class InventoryLedgerEntrySerializer(TenantOwnedSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    movement_type = serializers.CharField(source="movement.movement_type", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = InventoryLedgerEntry
        fields = [
            "id",
            "movement",
            "movement_type",
            "line",
            "variant",
            "variant_sku",
            "warehouse",
            "warehouse_code",
            "quantity_delta",
            "value_delta",
            "running_quantity",
            "running_value",
            "average_cost",
            "reference_type",
            "reference_id",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "movement",
            "movement_type",
            "line",
            "variant",
            "variant_sku",
            "warehouse",
            "warehouse_code",
            "quantity_delta",
            "value_delta",
            "running_quantity",
            "running_value",
            "average_cost",
            "reference_type",
            "reference_id",
            "note",
        )


class StockMovementSerializer(TenantOwnedSerializer):
    lines = StockMovementLineReadSerializer(many=True, read_only=True)
    ledger_entries = InventoryLedgerEntrySerializer(many=True, read_only=True)
    line_items = StockMovementLineWriteSerializer(many=True, write_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = StockMovement
        fields = [
            "id",
            "movement_type",
            "status",
            "reference_number",
            "description",
            "performed_by",
            "performed_at",
            "source_document_type",
            "source_document_id",
            "metadata",
            "lines",
            "ledger_entries",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "lines",
            "ledger_entries",
            "performed_by",
            "performed_at",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is None and not attrs.get("line_items"):
            raise serializers.ValidationError({"line_items": "Provide at least one movement line."})
        return attrs

    def create(self, validated_data):
        line_items_data = validated_data.pop("line_items", [])
        tenant = self._get_tenant()
        if tenant is None:
            raise serializers.ValidationError({"detail": "Tenant context missing."})

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not getattr(user, "is_authenticated", False):
            user = None

        lines = [
            StockMovementLineParams(
                variant=item["variant"],
                warehouse=item["warehouse"],
                quantity=item["quantity"],
                unit_cost=item.get("unit_cost"),
                metadata=item.get("metadata"),
                reference_type=item.get("reference_type", ""),
                reference_id=item.get("reference_id", ""),
                note=item.get("note", ""),
            )
            for item in line_items_data
        ]

        movement = InventoryService.record_movement(
            tenant=tenant,
            movement_type=validated_data.get("movement_type"),
            lines=lines,
            reference_number=validated_data.get("reference_number"),
            description=validated_data.get("description", ""),
            performed_by=user,
            source_document_type=validated_data.get("source_document_type", ""),
            source_document_id=validated_data.get("source_document_id", ""),
            metadata=validated_data.get("metadata"),
        )
        status = validated_data.get("status")
        if status and status != movement.status:
            movement.status = status
            movement.save(update_fields=["status", "updated_at"])
        return movement


class PurchaseOrderLineSerializer(TenantOwnedSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = PurchaseOrderLine
        fields = [
            "id",
            "order",
            "variant",
            "variant_sku",
            "variant_name",
            "description",
            "ordered_quantity",
            "received_quantity",
            "billed_quantity",
            "unit_price",
            "tax_rate",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "order",
            "variant_sku",
            "variant_name",
            "received_quantity",
            "billed_quantity",
        )


class PurchaseOrderLineWriteSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    description = serializers.CharField(required=False, allow_blank=True, default="")
    ordered_quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, default=Decimal("0"))
    tax_rate = serializers.DecimalField(max_digits=6, decimal_places=3, required=False, default=Decimal("0"))
    metadata = serializers.JSONField(required=False)


class PurchaseOrderSerializer(TenantOwnedSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    line_items = PurchaseOrderLineWriteSerializer(many=True, write_only=True, required=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = PurchaseOrder
        fields = [
            "id",
            "number",
            "supplier",
            "supplier_name",
            "status",
            "order_date",
            "expected_date",
            "currency",
            "subtotal",
            "tax_amount",
            "total_amount",
            "notes",
            "created_by",
            "lines",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "created_by",
            "subtotal",
            "tax_amount",
            "total_amount",
            "lines",
            "supplier_name",
        )

    def validate_supplier(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Supplier must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        tenant = self._get_tenant()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not getattr(user, "is_authenticated", False):
            user = None

        order = PurchaseOrder.objects.create(
            tenant=tenant,
            created_by=user,
            **validated_data,
        )
        if line_items:
            self._replace_lines(order, line_items)
        PurchasingService._update_order_status(order)
        return order

    def update(self, instance, validated_data):
        line_items = validated_data.pop("line_items", None)
        supplier = validated_data.get("supplier")
        if supplier is not None and supplier.tenant_id != instance.tenant_id:
            raise serializers.ValidationError({"supplier": "Supplier must belong to the current tenant."})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])

        if line_items is not None:
            instance.lines.all().delete()
            self._replace_lines(instance, line_items)
        PurchasingService._update_order_status(instance)
        return instance

    def _replace_lines(self, order: PurchaseOrder, line_items):
        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        tenant = order.tenant
        for item in line_items:
            variant = item["variant"]
            if variant.tenant_id != tenant.id:
                raise serializers.ValidationError(
                    {"line_items": f"Variant {variant.pk} does not belong to this tenant."}
                )
            ordered_quantity = item["ordered_quantity"]
            unit_price = item.get("unit_price") or Decimal("0")
            tax_rate = item.get("tax_rate") or Decimal("0")
            line_total = ordered_quantity * unit_price
            subtotal += line_total
            tax_amount += line_total * (tax_rate / Decimal("100"))
            PurchaseOrderLine.objects.create(
                tenant=tenant,
                order=order,
                variant=variant,
                description=item.get("description", ""),
                ordered_quantity=ordered_quantity,
                unit_price=unit_price,
                tax_rate=tax_rate,
                metadata=item.get("metadata") or {},
            )

        subtotal = subtotal.quantize(DECIMAL_PRECISION_CURRENCY)
        tax_amount = tax_amount.quantize(DECIMAL_PRECISION_CURRENCY)
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.total_amount = (subtotal + tax_amount).quantize(DECIMAL_PRECISION_CURRENCY)
        order.save(update_fields=["subtotal", "tax_amount", "total_amount", "updated_at"])


class PurchaseReceiptLineSerializer(TenantOwnedSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = PurchaseReceiptLine
        fields = [
            "id",
            "receipt",
            "order_line",
            "variant",
            "variant_sku",
            "quantity",
            "unit_cost",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("receipt", "variant_sku")


class PurchaseReceiptLineWriteSerializer(serializers.Serializer):
    order_line = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrderLine.objects.all(), required=False, allow_null=True
    )
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)


class PurchaseReceiptSerializer(TenantOwnedSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    lines = PurchaseReceiptLineSerializer(many=True, read_only=True)
    line_items = PurchaseReceiptLineWriteSerializer(many=True, write_only=True)
    auto_post = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = PurchaseReceipt
        fields = [
            "id",
            "order",
            "order_number",
            "number",
            "status",
            "receipt_date",
            "received_by",
            "warehouse",
            "stock_movement",
            "notes",
            "lines",
            "line_items",
            "auto_post",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "order_number",
            "stock_movement",
            "lines",
        )

    def validate_order(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Order must belong to the current tenant.")
        return value

    def validate_warehouse(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Warehouse must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        auto_post = validated_data.pop("auto_post", False)
        tenant = self._get_tenant()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not getattr(user, "is_authenticated", False):
            user = None

        receipt = PurchaseReceipt.objects.create(
            tenant=tenant,
            received_by=user if validated_data.get("received_by") is None else validated_data.get("received_by"),
            **validated_data,
        )

        for item in line_items:
            order_line = item.get("order_line")
            variant = item["variant"]
            if variant.tenant_id != tenant.id:
                raise serializers.ValidationError(
                    {"line_items": f"Variant {variant.pk} does not belong to this tenant."}
                )
            if order_line and order_line.order_id != receipt.order_id:
                raise serializers.ValidationError(
                    {"line_items": "Order line does not belong to the referenced purchase order."}
                )
            PurchaseReceiptLine.objects.create(
                tenant=tenant,
                receipt=receipt,
                order_line=order_line,
                variant=variant,
                quantity=item["quantity"],
                unit_cost=item.get("unit_cost") or Decimal("0"),
                metadata=item.get("metadata") or {},
            )

        if auto_post or receipt.status == PurchaseReceipt.Status.POSTED:
            PurchasingService.post_receipt(receipt, performed_by=user)
        return receipt


class PurchaseBillLineSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = PurchaseBillLine
        fields = [
            "id",
            "bill",
            "order_line",
            "description",
            "quantity",
            "unit_price",
            "tax_rate",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("bill",)


class PurchaseBillLineWriteSerializer(serializers.Serializer):
    order_line = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrderLine.objects.all(), required=False, allow_null=True
    )
    description = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, default=Decimal("0"))
    tax_rate = serializers.DecimalField(max_digits=6, decimal_places=3, required=False, default=Decimal("0"))
    metadata = serializers.JSONField(required=False)


class PurchaseBillSerializer(TenantOwnedSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    lines = PurchaseBillLineSerializer(many=True, read_only=True)
    line_items = PurchaseBillLineWriteSerializer(many=True, write_only=True, required=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = PurchaseBill
        fields = [
            "id",
            "order",
            "order_number",
            "number",
            "status",
            "bill_date",
            "due_date",
            "currency",
            "subtotal",
            "tax_amount",
            "total_amount",
            "notes",
            "lines",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "order_number",
            "subtotal",
            "tax_amount",
            "total_amount",
            "lines",
        )

    def validate_order(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Order must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        tenant = self._get_tenant()
        bill = PurchaseBill.objects.create(tenant=tenant, **validated_data)
        if line_items:
            self._replace_lines(bill, line_items)
        PurchasingService.post_bill(bill)
        return bill

    def update(self, instance, validated_data):
        line_items = validated_data.pop("line_items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        if line_items is not None:
            instance.lines.all().delete()
            self._replace_lines(instance, line_items)
        PurchasingService.post_bill(instance)
        return instance

    def _replace_lines(self, bill: PurchaseBill, line_items):
        tenant = bill.tenant
        bill.lines.all().delete()
        for item in line_items:
            order_line = item.get("order_line")
            if order_line and order_line.order_id != bill.order_id:
                raise serializers.ValidationError(
                    {"line_items": "Order line does not belong to the referenced purchase order."}
                )
            PurchaseBillLine.objects.create(
                tenant=tenant,
                bill=bill,
                order_line=order_line,
                description=item.get("description", ""),
                quantity=item["quantity"],
                unit_price=item.get("unit_price") or Decimal("0"),
                tax_rate=item.get("tax_rate") or Decimal("0"),
                metadata=item.get("metadata") or {},
            )


class PurchasePaymentSerializer(TenantOwnedSerializer):
    bill_number = serializers.CharField(source="bill.number", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = PurchasePayment
        fields = [
            "id",
            "bill",
            "bill_number",
            "number",
            "status",
            "payment_date",
            "amount",
            "method",
            "reference",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("bill_number",)

    def validate_bill(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Bill must belong to the current tenant.")
        return value

    def create(self, validated_data):
        tenant = self._get_tenant()
        payment = PurchasePayment.objects.create(tenant=tenant, **validated_data)
        PurchasingService.post_payment(payment)
        return payment

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        PurchasingService.post_payment(instance)
        return instance


class SalesOrderLineSerializer(TenantOwnedSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)
    variant_name = serializers.CharField(source="variant.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = SalesOrderLine
        fields = [
            "id",
            "order",
            "variant",
            "variant_sku",
            "variant_name",
            "description",
            "ordered_quantity",
            "delivered_quantity",
            "invoiced_quantity",
            "unit_price",
            "tax_rate",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "order",
            "variant_sku",
            "variant_name",
            "delivered_quantity",
            "invoiced_quantity",
        )


class SalesOrderLineWriteSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    description = serializers.CharField(required=False, allow_blank=True, default="")
    ordered_quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, default=Decimal("0"))
    tax_rate = serializers.DecimalField(max_digits=6, decimal_places=3, required=False, default=Decimal("0"))
    metadata = serializers.JSONField(required=False)


class SalesOrderSerializer(TenantOwnedSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    line_items = SalesOrderLineWriteSerializer(many=True, write_only=True, required=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = SalesOrder
        fields = [
            "id",
            "number",
            "customer",
            "customer_name",
            "status",
            "order_date",
            "ship_date",
            "currency",
            "subtotal",
            "tax_amount",
            "total_amount",
            "notes",
            "created_by",
            "lines",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "created_by",
            "subtotal",
            "tax_amount",
            "total_amount",
            "lines",
            "customer_name",
        )

    def validate_customer(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Customer must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        tenant = self._get_tenant()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not getattr(user, "is_authenticated", False):
            user = None

        order = SalesOrder.objects.create(
            tenant=tenant,
            created_by=user,
            **validated_data,
        )
        if line_items:
            self._replace_lines(order, line_items)
        SalesService._update_order_status(order)
        return order

    def update(self, instance, validated_data):
        line_items = validated_data.pop("line_items", None)
        customer = validated_data.get("customer")
        if customer is not None and customer.tenant_id != instance.tenant_id:
            raise serializers.ValidationError({"customer": "Customer must belong to the current tenant."})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])

        if line_items is not None:
            instance.lines.all().delete()
            self._replace_lines(instance, line_items)
        SalesService._update_order_status(instance)
        return instance

    def _replace_lines(self, order: SalesOrder, line_items):
        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        tenant = order.tenant
        for item in line_items:
            variant = item["variant"]
            if variant.tenant_id != tenant.id:
                raise serializers.ValidationError(
                    {"line_items": f"Variant {variant.pk} does not belong to this tenant."}
                )
            ordered_quantity = item["ordered_quantity"]
            unit_price = item.get("unit_price") or Decimal("0")
            tax_rate = item.get("tax_rate") or Decimal("0")
            line_total = ordered_quantity * unit_price
            subtotal += line_total
            tax_amount += line_total * (tax_rate / Decimal("100"))
            SalesOrderLine.objects.create(
                tenant=tenant,
                order=order,
                variant=variant,
                description=item.get("description", ""),
                ordered_quantity=ordered_quantity,
                unit_price=unit_price,
                tax_rate=tax_rate,
                metadata=item.get("metadata") or {},
            )

        subtotal = subtotal.quantize(DECIMAL_PRECISION_CURRENCY)
        tax_amount = tax_amount.quantize(DECIMAL_PRECISION_CURRENCY)
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.total_amount = (subtotal + tax_amount).quantize(DECIMAL_PRECISION_CURRENCY)
        order.save(update_fields=["subtotal", "tax_amount", "total_amount", "updated_at"])


class DeliveryNoteLineSerializer(TenantOwnedSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = DeliveryNoteLine
        fields = [
            "id",
            "delivery",
            "order_line",
            "variant",
            "variant_sku",
            "quantity",
            "unit_price",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("delivery", "variant_sku")


class DeliveryNoteLineWriteSerializer(serializers.Serializer):
    order_line = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrderLine.objects.all(), required=False, allow_null=True
    )
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, allow_null=True)
    metadata = serializers.JSONField(required=False)


class DeliveryNoteSerializer(TenantOwnedSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    lines = DeliveryNoteLineSerializer(many=True, read_only=True)
    line_items = DeliveryNoteLineWriteSerializer(many=True, write_only=True)
    auto_post = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = DeliveryNote
        fields = [
            "id",
            "order",
            "order_number",
            "number",
            "status",
            "delivery_date",
            "fulfilled_by",
            "warehouse",
            "stock_movement",
            "notes",
            "lines",
            "line_items",
            "auto_post",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("order_number", "stock_movement", "lines")

    def validate_order(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Order must belong to the current tenant.")
        return value

    def validate_warehouse(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Warehouse must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        auto_post = validated_data.pop("auto_post", False)
        tenant = self._get_tenant()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        fulfilled_by = validated_data.get("fulfilled_by") or (user if getattr(user, "is_authenticated", False) else None)

        delivery = DeliveryNote.objects.create(
            tenant=tenant,
            fulfilled_by=fulfilled_by,
            **validated_data,
        )

        for item in line_items:
            order_line = item.get("order_line")
            variant = item["variant"]
            if variant.tenant_id != tenant.id:
                raise serializers.ValidationError(
                    {"line_items": f"Variant {variant.pk} does not belong to this tenant."}
                )
            if order_line and order_line.order_id != delivery.order_id:
                raise serializers.ValidationError(
                    {"line_items": "Order line does not belong to the referenced sales order."}
                )
            DeliveryNoteLine.objects.create(
                tenant=tenant,
                delivery=delivery,
                order_line=order_line,
                variant=variant,
                quantity=item["quantity"],
                unit_price=item.get("unit_price") or Decimal("0"),
                metadata=item.get("metadata") or {},
            )

        if auto_post or delivery.status == DeliveryNote.Status.POSTED:
            performer = user if getattr(user, "is_authenticated", False) else None
            SalesService.post_delivery(delivery, performed_by=performer)
        return delivery


class SalesInvoiceLineSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = SalesInvoiceLine
        fields = [
            "id",
            "invoice",
            "order_line",
            "description",
            "quantity",
            "unit_price",
            "tax_rate",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("invoice",)


class SalesInvoiceLineWriteSerializer(serializers.Serializer):
    order_line = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrderLine.objects.all(), required=False, allow_null=True
    )
    description = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, default=Decimal("0"))
    tax_rate = serializers.DecimalField(max_digits=6, decimal_places=3, required=False, default=Decimal("0"))
    metadata = serializers.JSONField(required=False)


class SalesInvoiceSerializer(TenantOwnedSerializer):
    order_number = serializers.CharField(source="order.number", read_only=True)
    lines = SalesInvoiceLineSerializer(many=True, read_only=True)
    line_items = SalesInvoiceLineWriteSerializer(many=True, write_only=True, required=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = SalesInvoice
        fields = [
            "id",
            "order",
            "order_number",
            "number",
            "status",
            "invoice_date",
            "due_date",
            "currency",
            "subtotal",
            "tax_amount",
            "total_amount",
            "notes",
            "lines",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "order_number",
            "subtotal",
            "tax_amount",
            "total_amount",
            "lines",
        )

    def validate_order(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Order must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        tenant = self._get_tenant()
        invoice = SalesInvoice.objects.create(tenant=tenant, **validated_data)
        if line_items:
            self._replace_lines(invoice, line_items)
        SalesService.post_invoice(invoice)
        return invoice

    def update(self, instance, validated_data):
        line_items = validated_data.pop("line_items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        if line_items is not None:
            instance.lines.all().delete()
            self._replace_lines(instance, line_items)
        SalesService.post_invoice(instance)
        return instance

    def _replace_lines(self, invoice: SalesInvoice, line_items):
        tenant = invoice.tenant
        for item in line_items:
            order_line = item.get("order_line")
            if order_line and order_line.order_id != invoice.order_id:
                raise serializers.ValidationError(
                    {"line_items": "Order line does not belong to the referenced sales order."}
                )
            SalesInvoiceLine.objects.create(
                tenant=tenant,
                invoice=invoice,
                order_line=order_line,
                description=item.get("description", ""),
                quantity=item["quantity"],
                unit_price=item.get("unit_price") or Decimal("0"),
                tax_rate=item.get("tax_rate") or Decimal("0"),
                metadata=item.get("metadata") or {},
            )


class SalesPaymentSerializer(TenantOwnedSerializer):
    invoice_number = serializers.CharField(source="invoice.number", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = SalesPayment
        fields = [
            "id",
            "invoice",
            "invoice_number",
            "number",
            "status",
            "payment_date",
            "amount",
            "method",
            "reference",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("invoice_number",)

    def validate_invoice(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Invoice must belong to the current tenant.")
        return value

    def create(self, validated_data):
        tenant = self._get_tenant()
        payment = SalesPayment.objects.create(tenant=tenant, **validated_data)
        SalesService.post_payment(payment)
        return payment

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])
        SalesService.post_payment(instance)
        return instance


class SalesRefundSerializer(TenantOwnedSerializer):
    invoice_number = serializers.CharField(source="invoice.number", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = SalesRefund
        fields = [
            "id",
            "invoice",
            "invoice_number",
            "number",
            "refund_date",
            "amount",
            "reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("invoice_number",)

    def validate_invoice(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Invoice must belong to the current tenant.")
        return value

    def create(self, validated_data):
        tenant = self._get_tenant()
        refund = SalesRefund.objects.create(tenant=tenant, **validated_data)
        SalesService.register_refund(refund)
        return refund


class MenuSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = Menu
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]


class MenuSectionSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = MenuSection
        fields = [
            "id",
            "menu",
            "name",
            "description",
            "sort_order",
            "created_at",
            "updated_at",
        ]

    def validate_menu(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Menu must belong to the current tenant.")
        return value


class MenuItemSerializer(TenantOwnedSerializer):
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = MenuItem
        fields = [
            "id",
            "section",
            "section_name",
            "name",
            "description",
            "sku",
            "base_price",
            "is_active",
            "preparation_time_seconds",
            "variant",
            "tags",
            "created_at",
            "updated_at",
        ]

    def validate_section(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Section must belong to the current tenant.")
        return value

    def validate_variant(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Variant must belong to the current tenant.")
        return value


class MenuModifierGroupSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = MenuModifierGroup
        fields = [
            "id",
            "item",
            "name",
            "is_required",
            "min_required",
            "max_allowed",
            "sort_order",
            "created_at",
            "updated_at",
        ]

    def validate_item(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Item must belong to the current tenant.")
        return value


class MenuModifierOptionSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = MenuModifierOption
        fields = [
            "id",
            "group",
            "name",
            "price_delta",
            "variant",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_group(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Modifier group must belong to the current tenant.")
        return value

    def validate_variant(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Variant must belong to the current tenant.")
        return value


class RecipeComponentSerializer(TenantOwnedSerializer):
    ingredient_sku = serializers.CharField(source="ingredient.sku", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = RecipeComponent
        fields = [
            "id",
            "recipe",
            "ingredient",
            "ingredient_sku",
            "quantity",
            "uom",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "ingredient_sku",
        )

    def validate_recipe(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Recipe must belong to the current tenant.")
        return value

    def validate_ingredient(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Ingredient must belong to the current tenant.")
        return value

    def validate_uom(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Unit must belong to the current tenant.")
        return value


class RecipeSerializer(TenantOwnedSerializer):
    components = RecipeComponentSerializer(many=True, read_only=True)
    component_items = RecipeComponentSerializer(many=True, write_only=True, required=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = Recipe
        fields = [
            "id",
            "item",
            "instructions",
            "yield_quantity",
            "yield_uom",
            "components",
            "component_items",
            "created_at",
            "updated_at",
        ]

    def validate_item(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Menu item must belong to the current tenant.")
        return value

    def validate_yield_uom(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Unit must belong to the current tenant.")
        return value

    def create(self, validated_data):
        components = validated_data.pop("component_items", [])
        recipe = super().create(validated_data)
        self._sync_components(recipe, components)
        return recipe

    def update(self, instance, validated_data):
        components = validated_data.pop("component_items", None)
        recipe = super().update(instance, validated_data)
        if components is not None:
            recipe.components.all().delete()
            self._sync_components(recipe, components)
        return recipe

    def _sync_components(self, recipe: Recipe, components: list[dict]) -> None:
        tenant = self._get_tenant()
        if tenant is None:
            tenant = recipe.tenant
        for payload in components:
            RecipeComponent.objects.create(
                tenant=tenant,
                recipe=recipe,
                ingredient=payload["ingredient"],
                quantity=payload["quantity"],
                uom=payload["uom"],
                notes=payload.get("notes", ""),
            )


class KitchenOrderLineSerializer(TenantOwnedSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = KitchenOrderLine
        fields = [
            "id",
            "ticket",
            "item",
            "item_name",
            "quantity",
            "modifiers",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "item_name",
            "ticket",
        )


class KitchenOrderLineWriteSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.DecimalField(max_digits=10, decimal_places=3, default=Decimal("1"))
    modifiers = serializers.JSONField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class KitchenDisplayEventSerializer(TenantOwnedSerializer):
    ticket_number = serializers.CharField(source="ticket.ticket_number", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = KitchenDisplayEvent
        fields = [
            "id",
            "ticket",
            "ticket_number",
            "action",
            "actor",
            "metadata",
            "occurred_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "ticket",
            "ticket_number",
            "occurred_at",
        )


class KitchenOrderTicketSerializer(TenantOwnedSerializer):
    lines = KitchenOrderLineSerializer(many=True, read_only=True)
    line_items = KitchenOrderLineWriteSerializer(many=True, write_only=True)
    events = KitchenDisplayEventSerializer(many=True, read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = KitchenOrderTicket
        fields = [
            "id",
            "ticket_number",
            "status",
            "source",
            "table_number",
            "notes",
            "placed_at",
            "completed_at",
            "lines",
            "line_items",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "lines",
            "events",
            "completed_at",
        )

    def create(self, validated_data):
        line_payload = validated_data.pop("line_items", [])
        tenant = self._get_tenant()
        ticket = super().create(validated_data)
        RestaurantService.create_ticket(
            tenant=tenant,
            ticket=ticket,
            lines=[
                {
                    "item": entry["item"],
                    "quantity": entry.get("quantity", Decimal("1")),
                    "modifiers": entry.get("modifiers", []),
                    "notes": entry.get("notes", ""),
                }
                for entry in line_payload
            ],
        )
        dispatch_kitchen_ticket.delay(str(ticket.id))
        return ticket


class KitchenDisplayActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=KitchenDisplayEvent.Action.choices)
    actor = serializers.CharField(required=False, allow_blank=True)


class QROrderingTokenSerializer(TenantOwnedSerializer):
    menu_name = serializers.CharField(source="menu.name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = QROrderingToken
        fields = [
            "id",
            "token",
            "menu",
            "menu_name",
            "table_number",
            "expires_at",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("menu_name",)

    def validate_menu(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Menu must belong to the current tenant.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("expires_at") and attrs["expires_at"] <= timezone.now():
            raise serializers.ValidationError({"expiresAt": "Expiration must be in the future."})
        return attrs


class POSShiftSerializer(TenantOwnedSerializer):
    opened_by_name = serializers.CharField(source="opened_by.full_name", read_only=True)
    closed_by_name = serializers.CharField(source="closed_by.full_name", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = POSShift
        fields = [
            "id",
            "register_code",
            "status",
            "opened_at",
            "closed_at",
            "opened_by",
            "opened_by_name",
            "closed_by",
            "closed_by_name",
            "opening_float",
            "closing_float",
            "notes",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "opened_by_name",
            "closed_by_name",
        )

    def create(self, validated_data):
        tenant = self._get_tenant()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and not getattr(user, "is_authenticated", False):
            user = None
        if validated_data.get("opened_by") is None:
            validated_data["opened_by"] = user
        shift = POSShift.objects.create(tenant=tenant, **validated_data)
        return shift


class POSSaleItemSerializer(TenantOwnedSerializer):
    variant_sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = POSSaleItem
        fields = [
            "id",
            "sale",
            "variant",
            "variant_sku",
            "quantity",
            "unit_price",
            "discount",
            "tax_rate",
            "line_total",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("sale", "variant_sku", "line_total")


class POSSaleItemWriteSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.DecimalField(max_digits=16, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=16, decimal_places=4)
    discount = serializers.DecimalField(max_digits=16, decimal_places=4, required=False, default=Decimal("0"))
    tax_rate = serializers.DecimalField(max_digits=6, decimal_places=3, required=False, default=Decimal("0"))
    metadata = serializers.JSONField(required=False)


class POSSalePaymentSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = POSSalePayment
        fields = [
            "id",
            "sale",
            "method",
            "amount",
            "received_at",
            "reference",
            "metadata",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("sale",)


class POSSalePaymentWriteSerializer(serializers.Serializer):
    method = serializers.CharField()
    amount = serializers.DecimalField(max_digits=16, decimal_places=4)
    received_at = serializers.DateTimeField(required=False)
    reference = serializers.CharField(required=False, allow_blank=True, default="")
    metadata = serializers.JSONField(required=False)
    status = serializers.ChoiceField(choices=POSSalePayment.Status.choices, default=POSSalePayment.Status.POSTED)


class POSSaleSerializer(TenantOwnedSerializer):
    shift_code = serializers.CharField(source="shift.register_code", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    items = POSSaleItemSerializer(many=True, read_only=True)
    payments = POSSalePaymentSerializer(many=True, read_only=True)
    line_items = POSSaleItemWriteSerializer(many=True, write_only=True)
    payment_items = POSSalePaymentWriteSerializer(many=True, write_only=True, required=False)
    auto_finalize = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta(TenantOwnedSerializer.Meta):
        model = POSSale
        fields = [
            "id",
            "shift",
            "shift_code",
            "warehouse",
            "reference",
            "status",
            "customer",
            "customer_name",
            "subtotal",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "change_due",
            "notes",
            "metadata",
            "stock_movement",
            "items",
            "payments",
            "line_items",
            "payment_items",
            "auto_finalize",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + (
            "shift_code",
            "customer_name",
            "subtotal",
            "tax_amount",
            "total_amount",
            "paid_amount",
            "change_due",
            "items",
            "payments",
            "stock_movement",
        )

    def validate_shift(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Shift must belong to the current tenant.")
        return value

    def validate_warehouse(self, value):
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Warehouse must belong to the current tenant.")
        return value

    def validate_customer(self, value):
        if value is None:
            return value
        tenant = self._get_tenant()
        if tenant is None or value.tenant_id != tenant.id:
            raise serializers.ValidationError("Customer must belong to the current tenant.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        payment_items = validated_data.pop("payment_items", [])
        auto_finalize = validated_data.pop("auto_finalize", False)

        tenant = self._get_tenant()
        sale = POSSale.objects.create(tenant=tenant, **validated_data)
        self._replace_items(sale, line_items)
        if payment_items:
            self._replace_payments(sale, payment_items)
        POSService.recalculate_sale_totals(sale)

        request = self.context.get("request")
        performer = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        if auto_finalize or sale.status == POSSale.Status.PAID:
            POSService.finalize_sale(sale, performed_by=performer)
        return sale

    def update(self, instance, validated_data):
        line_items = validated_data.pop("line_items", None)
        payment_items = validated_data.pop("payment_items", None)
        auto_finalize = validated_data.pop("auto_finalize", False)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=[*validated_data.keys(), "updated_at"])

        if line_items is not None:
            instance.items.all().delete()
            self._replace_items(instance, line_items)
        if payment_items is not None:
            instance.payments.all().delete()
            self._replace_payments(instance, payment_items)

        POSService.recalculate_sale_totals(instance)
        request = self.context.get("request")
        performer = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        if auto_finalize or instance.status == POSSale.Status.PAID:
            POSService.finalize_sale(instance, performed_by=performer)
        return instance

    def _replace_items(self, sale: POSSale, line_items):
        tenant = sale.tenant
        for item in line_items:
            variant = item["variant"]
            if variant.tenant_id != tenant.id:
                raise serializers.ValidationError(
                    {"line_items": f"Variant {variant.pk} does not belong to this tenant."}
                )
            POSSaleItem.objects.create(
                tenant=tenant,
                sale=sale,
                variant=variant,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                discount=item.get("discount") or Decimal("0"),
                tax_rate=item.get("tax_rate") or Decimal("0"),
                metadata=item.get("metadata") or {},
            )

    def _replace_payments(self, sale: POSSale, payment_items):
        tenant = sale.tenant
        for item in payment_items:
            POSSalePayment.objects.create(
                tenant=tenant,
                sale=sale,
                method=item["method"],
                amount=item["amount"],
                received_at=item.get("received_at") or sale.created_at,
                reference=item.get("reference", ""),
                metadata=item.get("metadata") or {},
                status=item.get("status") or POSSalePayment.Status.POSTED,
            )


class POSReceiptSerializer(TenantOwnedSerializer):
    sale_reference = serializers.CharField(source="sale.reference", read_only=True)

    class Meta(TenantOwnedSerializer.Meta):
        model = POSReceipt
        fields = [
            "id",
            "sale",
            "sale_reference",
            "number",
            "rendered_payload",
            "printed_at",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = TenantOwnedSerializer.Meta.read_only_fields + ("sale_reference",)


class POSOfflineQueueItemSerializer(TenantOwnedSerializer):
    class Meta(TenantOwnedSerializer.Meta):
        model = POSOfflineQueueItem
        fields = [
            "id",
            "operation",
            "payload",
            "status",
            "error_message",
            "synced_at",
            "created_at",
            "updated_at",
        ]









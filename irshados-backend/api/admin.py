from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    AuditLog,
    BlacklistedToken,
    Customer,
    Invitation,
    Membership,
    Permission,
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


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("full_name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "full_name", "password1", "password2")}),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "timezone", "is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug", "domain")
    list_filter = ("is_active", "timezone")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "slug", "is_system")
    list_filter = ("tenant", "is_system")
    search_fields = ("name", "slug", "tenant__name")
    autocomplete_fields = ("tenant",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("tenant", "user", "role", "status", "created_at")
    list_filter = ("tenant", "role", "status")
    search_fields = ("tenant__name", "tenant__slug", "user__email")
    autocomplete_fields = ("tenant", "user", "role")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "tenant", "role", "status", "expires_at")
    list_filter = ("tenant", "status")
    search_fields = ("email", "tenant__name", "tenant__slug")
    autocomplete_fields = ("tenant", "role", "invited_by")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "tenant", "user", "status_code", "created_at")
    list_filter = ("status_code", "tenant")
    search_fields = ("action", "path", "user__email")
    autocomplete_fields = ("tenant", "user")
    readonly_fields = (
        "action",
        "tenant",
        "user",
        "status_code",
        "method",
        "path",
        "request_payload",
        "response_payload",
        "ip_address",
        "created_at",
    )


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = ("jti", "created_at")
    search_fields = ("jti",)


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "tenant", "is_active", "updated_at")
    list_filter = ("tenant", "category", "is_active")
    search_fields = ("code", "name", "symbol")
    autocomplete_fields = ("tenant", "base_unit")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "parent", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("code", "name")
    autocomplete_fields = ("tenant", "parent")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "category", "track_inventory", "is_active")
    list_filter = ("tenant", "category", "track_inventory", "is_active")
    search_fields = ("code", "name", "description")
    autocomplete_fields = ("tenant", "category", "base_uom", "default_tax")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "tenant", "product", "track_inventory", "is_active")
    list_filter = ("tenant", "track_inventory", "is_active")
    search_fields = ("sku", "name", "barcode")
    autocomplete_fields = ("tenant", "product", "sales_uom")


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "scope", "rate", "is_inclusive", "is_compound")
    list_filter = ("tenant", "scope", "is_inclusive", "is_compound")
    search_fields = ("code", "name")
    autocomplete_fields = ("tenant",)


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "usage", "currency", "is_default", "is_active")
    list_filter = ("tenant", "usage", "is_default", "is_active")
    search_fields = ("code", "name")
    autocomplete_fields = ("tenant",)


@admin.register(PriceListItem)
class PriceListItemAdmin(admin.ModelAdmin):
    list_display = ("price_list", "variant", "tenant", "min_quantity", "price", "currency")
    list_filter = ("tenant", "price_list")
    search_fields = ("price_list__code", "variant__sku", "variant__name")
    autocomplete_fields = ("tenant", "price_list", "variant")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "is_default")
    list_filter = ("tenant", "is_default")
    search_fields = ("code", "name", "description")
    autocomplete_fields = ("tenant",)


@admin.register(WarehouseBin)
class WarehouseBinAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "warehouse", "bin_type", "is_default")
    list_filter = ("tenant", "bin_type", "is_default")
    search_fields = ("code", "name", "warehouse__code")
    autocomplete_fields = ("tenant", "warehouse")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "email", "phone", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("code", "name", "contact_name", "email")
    autocomplete_fields = ("tenant",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "email", "phone", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("code", "name", "email", "phone")
    autocomplete_fields = ("tenant",)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active", "updated_at")
    list_filter = ("tenant", "is_active")
    search_fields = ("name", "tenant__name")
    autocomplete_fields = ("tenant",)


@admin.register(MenuSection)
class MenuSectionAdmin(admin.ModelAdmin):
    list_display = ("name", "menu", "sort_order")
    list_filter = ("menu",)
    search_fields = ("name", "menu__name")
    autocomplete_fields = ("tenant", "menu")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "base_price", "is_active")
    list_filter = ("section", "is_active")
    search_fields = ("name", "section__menu__name", "sku")
    autocomplete_fields = ("tenant", "section", "variant")


@admin.register(MenuModifierGroup)
class MenuModifierGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "item", "is_required", "min_required", "max_allowed")
    list_filter = ("item", "is_required")
    search_fields = ("name", "item__name")
    autocomplete_fields = ("tenant", "item")


@admin.register(MenuModifierOption)
class MenuModifierOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "price_delta", "is_active")
    list_filter = ("group", "is_active")
    search_fields = ("name", "group__item__name")
    autocomplete_fields = ("tenant", "group", "variant")


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("item", "yield_quantity", "yield_uom")
    list_filter = ("yield_uom",)
    search_fields = ("item__name",)
    autocomplete_fields = ("tenant", "item", "yield_uom")


@admin.register(RecipeComponent)
class RecipeComponentAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "quantity", "uom")
    list_filter = ("ingredient",)
    search_fields = ("recipe__item__name", "ingredient__sku")
    autocomplete_fields = ("tenant", "recipe", "ingredient", "uom")


@admin.register(KitchenOrderTicket)
class KitchenOrderTicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "tenant", "status", "source", "placed_at")
    list_filter = ("tenant", "status", "source")
    search_fields = ("ticket_number", "table_number")
    autocomplete_fields = ("tenant",)


@admin.register(KitchenOrderLine)
class KitchenOrderLineAdmin(admin.ModelAdmin):
    list_display = ("ticket", "item", "quantity")
    list_filter = ("ticket", "item")
    search_fields = ("ticket__ticket_number", "item__name")
    autocomplete_fields = ("tenant", "ticket", "item")


@admin.register(KitchenDisplayEvent)
class KitchenDisplayEventAdmin(admin.ModelAdmin):
    list_display = ("ticket", "action", "actor", "occurred_at")
    list_filter = ("action",)
    search_fields = ("ticket__ticket_number", "actor")
    autocomplete_fields = ("tenant", "ticket")


@admin.register(QROrderingToken)
class QROrderingTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "tenant", "menu", "table_number", "expires_at", "is_active")
    list_filter = ("tenant", "is_active")
    search_fields = ("token", "table_number")
    autocomplete_fields = ("tenant", "menu")


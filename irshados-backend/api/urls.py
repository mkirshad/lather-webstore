from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    CurrentTenantView,
    DeliveryNoteViewSet,
    InvitationAcceptView,
    InvitationCreateView,
    InventoryBalanceViewSet,
    InventoryLedgerEntryViewSet,
    InventorySummaryReportView,
    POSOfflineQueueViewSet,
    POSReceiptViewSet,
    POSShiftViewSet,
    POSSaleViewSet,
    PurchaseBillViewSet,
    PurchaseOrderViewSet,
    PurchasePaymentViewSet,
    PurchaseReceiptViewSet,
    PriceListItemViewSet,
    PriceListViewSet,
    ProductCategoryViewSet,
    ProductVariantViewSet,
    ProductViewSet,
    SalesInvoiceViewSet,
    SalesOrderViewSet,
    SalesPaymentViewSet,
    SalesRefundViewSet,
    MenuViewSet,
    MenuSectionViewSet,
    MenuItemViewSet,
    MenuModifierGroupViewSet,
    MenuModifierOptionViewSet,
    RecipeViewSet,
    RecipeComponentViewSet,
    KitchenDisplayEventViewSet,
    KitchenOrderTicketViewSet,
    QROrderingTokenViewSet,
    PurchasingPipelineReportView,
    SalesPipelineReportView,
    SessionRefreshView,
    SignInView,
    SignOutView,
    SignUpView,
    StockMovementViewSet,
    SupplierViewSet,
    TaxViewSet,
    TenantSwitchView,
    UnitOfMeasureViewSet,
    WarehouseBinViewSet,
    WarehouseViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register("masters/uoms", UnitOfMeasureViewSet, basename="uom")
router.register("masters/categories", ProductCategoryViewSet, basename="product-category")
router.register("masters/products", ProductViewSet, basename="product")
router.register("masters/variants", ProductVariantViewSet, basename="product-variant")
router.register("masters/taxes", TaxViewSet, basename="tax")
router.register("masters/price-lists", PriceListViewSet, basename="price-list")
router.register("masters/price-list-items", PriceListItemViewSet, basename="price-list-item")
router.register("inventory/movements", StockMovementViewSet, basename="stock-movement")
router.register("inventory/ledger", InventoryLedgerEntryViewSet, basename="inventory-ledger")
router.register("inventory/balances", InventoryBalanceViewSet, basename="inventory-balance")
router.register("inventory/warehouses", WarehouseViewSet, basename="warehouse")
router.register("inventory/bins", WarehouseBinViewSet, basename="warehouse-bin")
router.register("purchasing/suppliers", SupplierViewSet, basename="supplier")
router.register("purchasing/orders", PurchaseOrderViewSet, basename="purchase-order")
router.register("purchasing/receipts", PurchaseReceiptViewSet, basename="purchase-receipt")
router.register("purchasing/bills", PurchaseBillViewSet, basename="purchase-bill")
router.register("purchasing/payments", PurchasePaymentViewSet, basename="purchase-payment")
router.register("sales/orders", SalesOrderViewSet, basename="sales-order")
router.register("sales/deliveries", DeliveryNoteViewSet, basename="delivery-note")
router.register("sales/invoices", SalesInvoiceViewSet, basename="sales-invoice")
router.register("sales/payments", SalesPaymentViewSet, basename="sales-payment")
router.register("sales/refunds", SalesRefundViewSet, basename="sales-refund")
router.register("sales/customers", CustomerViewSet, basename="customer")
router.register("restaurant/menus", MenuViewSet, basename="restaurant-menu")
router.register("restaurant/menu-sections", MenuSectionViewSet, basename="restaurant-menu-section")
router.register("restaurant/menu-items", MenuItemViewSet, basename="restaurant-menu-item")
router.register("restaurant/modifier-groups", MenuModifierGroupViewSet, basename="restaurant-modifier-group")
router.register("restaurant/modifier-options", MenuModifierOptionViewSet, basename="restaurant-modifier-option")
router.register("restaurant/recipes", RecipeViewSet, basename="restaurant-recipe")
router.register("restaurant/recipe-components", RecipeComponentViewSet, basename="restaurant-recipe-component")
router.register("restaurant/kitchen-events", KitchenDisplayEventViewSet, basename="restaurant-kds-event")
router.register("restaurant/kitchen-tickets", KitchenOrderTicketViewSet, basename="restaurant-kot")
router.register("restaurant/qr-tokens", QROrderingTokenViewSet, basename="restaurant-qr-token")
router.register("pos/shifts", POSShiftViewSet, basename="pos-shift")
router.register("pos/sales", POSSaleViewSet, basename="pos-sale")
router.register("pos/receipts", POSReceiptViewSet, basename="pos-receipt")
router.register("pos/offline-queue", POSOfflineQueueViewSet, basename="pos-offline-queue")

urlpatterns = [
    path("sign-up", SignUpView.as_view(), name="sign-up"),
    path("sign-in", SignInView.as_view(), name="sign-in"),
    path("sign-out", SignOutView.as_view(), name="sign-out"),
    path("tenants/current", CurrentTenantView.as_view(), name="current-tenant"),
    path("invites", InvitationCreateView.as_view(), name="invite-create"),
    path("invites/accept", InvitationAcceptView.as_view(), name="invite-accept"),
    path("sessions/switch-tenant", TenantSwitchView.as_view(), name="switch-tenant"),
    path("sessions/refresh", SessionRefreshView.as_view(), name="token-refresh"),
    path(
        "reports/inventory-summary",
        InventorySummaryReportView.as_view(),
        name="reports-inventory-summary",
    ),
    path(
        "reports/purchasing-pipeline",
        PurchasingPipelineReportView.as_view(),
        name="reports-purchasing-pipeline",
    ),
    path(
        "reports/sales-pipeline",
        SalesPipelineReportView.as_view(),
        name="reports-sales-pipeline",
    ),
    path("", include(router.urls)),
]



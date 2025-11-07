from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, F, Q, Sum, Max
from django.utils import timezone
from rest_framework import exceptions, permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .permissions import HasTenantPermissions, require_tenant_permissions
from .serializers import (
    CustomerSerializer,
    InventoryBalanceSerializer,
    InventoryLedgerEntrySerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    KitchenDisplayActionSerializer,
    KitchenDisplayEventSerializer,
    KitchenOrderTicketSerializer,
    MenuItemSerializer,
    MenuModifierGroupSerializer,
    MenuModifierOptionSerializer,
    MenuSectionSerializer,
    MenuSerializer,
    RecipeComponentSerializer,
    RecipeSerializer,
    QROrderingTokenSerializer,
    PriceListItemSerializer,
    PriceListSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    PurchaseBillSerializer,
    PurchaseOrderSerializer,
    PurchasePaymentSerializer,
    PurchaseReceiptSerializer,
    DeliveryNoteSerializer,
    POSOfflineQueueItemSerializer,
    POSReceiptSerializer,
    POSShiftSerializer,
    POSSaleSerializer,
    SalesInvoiceSerializer,
    SalesOrderSerializer,
    SalesPaymentSerializer,
    SalesRefundSerializer,
    SignInSerializer,
    SignUpSerializer,
    StockMovementSerializer,
    SupplierSerializer,
    TaxSerializer,
    TenantSummarySerializer,
    TenantSwitchSerializer,
    UnitOfMeasureSerializer,
    UserSerializer,
    WarehouseBinSerializer,
    WarehouseSerializer,
)
from .tenant import activate_tenant
from .models import (
    Customer,
    InventoryBalance,
    InventoryLedgerEntry,
    PriceList,
    PriceListItem,
    Product,
    ProductCategory,
    ProductVariant,
    PurchaseBill,
    PurchaseOrder,
    PurchasePayment,
    PurchaseReceipt,
    DeliveryNote,
    POSOfflineQueueItem,
    POSReceipt,
    POSShift,
    POSSale,
    SalesInvoice,
    SalesOrder,
    SalesPayment,
    SalesRefund,
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
    StockMovement,
    Supplier,
    Tax,
    UnitOfMeasure,
    Warehouse,
    WarehouseBin,
)
from .pagination import TenantCursorPagination
from .services.purchasing import PurchasingService
from .services.sales import SalesService
from .services.pos import POSService
from .services.restaurant import RestaurantService
from .services.inventory import DECIMAL_PRECISION_CURRENCY


def _set_audit_action(request, action: str) -> None:
    setattr(request, "audit_action", action)
    raw_request = getattr(request, "_request", None)
    if raw_request is not None:
        setattr(raw_request, "audit_action", action)


def _issue_tokens(user, membership) -> dict:
    refresh = RefreshToken.for_user(user)
    refresh["tenant_id"] = str(membership.tenant_id)
    refresh["tenant_slug"] = membership.tenant.slug
    refresh["role"] = membership.role.slug
    access_token = refresh.access_token
    access_token["tenant_id"] = str(membership.tenant_id)
    access_token["tenant_slug"] = membership.tenant.slug
    access_token["role"] = membership.role.slug

    with activate_tenant(membership.tenant):
        serializer = UserSerializer(user, context={"active_membership": membership})
        user_payload = serializer.data

    user_payload.update(
        {
            "userId": str(user.id),
            "userName": user.full_name,
            "email": user.email,
            "authority": [membership.role.slug],
        }
    )

    membership_payload = TenantSummarySerializer(membership).data

    return {
        "accessToken": str(access_token),
        "refreshToken": str(refresh),
        "user": user_payload,
        "membership": membership_payload,
    }


class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        _set_audit_action(request, "auth.sign_up")
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        payload = _issue_tokens(result["user"], result["membership"])
        return response.Response(payload, status=status.HTTP_201_CREATED)


class SignInView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        _set_audit_action(request, "auth.sign_in")
        serializer = SignInSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        payload = _issue_tokens(result["user"], result["membership"])
        return response.Response(payload)


class SignOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        _set_audit_action(request, "auth.sign_out")
        refresh_token = request.data.get("refreshToken")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                raise exceptions.ValidationError({"refreshToken": "Invalid refresh token."})
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class CurrentTenantView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        membership = getattr(request, "membership", None)
        if tenant is None or membership is None:
            raise exceptions.ValidationError(
                {"detail": "An active tenant context is required. Provide the X-Tenant header."}
            )

        serializer = TenantSummarySerializer(membership)
        payload = serializer.data
        payload.update(
            {
                "timezone": tenant.timezone,
                "branding": tenant.branding,
                "settings": tenant.settings,
            }
        )
        return response.Response(payload)


@require_tenant_permissions("tenant.manage")
class InvitationCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasTenantPermissions]

    def post(self, request):
        _set_audit_action(request, "tenant.invite.create")
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise exceptions.ValidationError(
                {"detail": "Provide the X-Tenant header to create invitations."}
            )
        serializer = InvitationCreateSerializer(
            data=request.data,
            context={"tenant": tenant, "invited_by": request.user},
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        payload = {
            "id": str(invitation.id),
            "email": invitation.email,
            "role": invitation.role.slug,
            "expiresAt": invitation.expires_at.isoformat(),
            "status": invitation.status,
        }
        return response.Response(payload, status=status.HTTP_201_CREATED)


class InvitationAcceptView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        _set_audit_action(request, "auth.invite.accept")
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        payload = _issue_tokens(result["user"], result["membership"])
        return response.Response(payload, status=status.HTTP_200_OK)


class TenantSwitchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        _set_audit_action(request, "auth.switch_tenant")
        serializer = TenantSwitchSerializer(
            data=request.data,
            context={"user": request.user},
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        payload = _issue_tokens(result["user"], result["membership"])
        return response.Response(payload)


class SessionRefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        _set_audit_action(request, "auth.refresh")
        refresh_token = request.data.get("refreshToken")
        if not refresh_token:
            raise exceptions.ValidationError({"refreshToken": "This field is required."})

        try:
            token = RefreshToken(refresh_token)
        except TokenError as exc:
            raise exceptions.ValidationError({"refreshToken": str(exc)}) from exc

        from .models import Membership, Tenant, User  # late import to avoid circular

        user = User.objects.filter(id=token.get("user_id")).first()
        if user is None:
            raise exceptions.ValidationError({"refreshToken": "User not found."})

        tenant_id = token.get("tenant_id")
        tenant_slug = token.get("tenant_slug")
        tenant = None
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None and tenant_slug:
            tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if tenant is None:
            raise exceptions.ValidationError({"refreshToken": "Tenant context missing."})

        tenant.ensure_system_roles()
        with activate_tenant(tenant):
            membership = (
                Membership.objects.select_related("tenant", "role")
                .filter(tenant=tenant, user=user, status=Membership.Status.ACTIVE)
                .first()
            )
        if membership is None:
            raise exceptions.ValidationError({"refreshToken": "Membership no longer active."})

        token.blacklist()
        payload = _issue_tokens(user, membership)
        return response.Response(payload)


class TenantModelViewSet(viewsets.ModelViewSet):
    """Base ViewSet enforcing tenant scoping and permission mapping."""

    pagination_class = TenantCursorPagination
    permission_classes = [permissions.IsAuthenticated, HasTenantPermissions]
    view_permissions: tuple[str, ...] = ()
    edit_permissions: tuple[str, ...] = ()
    delete_permissions: tuple[str, ...] | None = None

    def get_permissions(self):
        action = getattr(self, "action", None)
        if action in ("list", "retrieve"):
            required = self.view_permissions or getattr(self, "required_permissions", ())
        elif action in ("create", "update", "partial_update"):
            required = self.edit_permissions or self.view_permissions
        elif action == "destroy":
            required = self.delete_permissions or self.edit_permissions or self.view_permissions
        else:
            required = getattr(self, "required_permissions", ()) or self.view_permissions

        if not required:
            raise exceptions.PermissionDenied("This endpoint is not currently permissioned.")

        self.required_permissions = required
        return super().get_permissions()

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        queryset = super().get_queryset()
        if tenant is None:
            return queryset.none()
        return queryset.filter(tenant=tenant)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return self.apply_filters(queryset)

    def apply_filters(self, queryset):
        return queryset


class UnitOfMeasureViewSet(TenantModelViewSet):
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(symbol__icontains=search)
            )
        category = params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class ProductCategoryViewSet(TenantModelViewSet):
    queryset = ProductCategory.objects.select_related("parent").all()
    serializer_class = ProductCategorySerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        parent = params.get("parent")
        if parent:
            queryset = queryset.filter(parent_id=parent)
        return queryset


class TaxViewSet(TenantModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        scope = params.get("scope")
        if scope:
            queryset = queryset.filter(scope=scope)
        return queryset


class ProductViewSet(TenantModelViewSet):
    queryset = Product.objects.select_related("category", "base_uom", "default_tax").all()
    serializer_class = ProductSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(description__icontains=search)
            )
        category = params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        track_inventory = params.get("track_inventory")
        if track_inventory in {"true", "false"}:
            queryset = queryset.filter(track_inventory=track_inventory.lower() == "true")
        return queryset


class ProductVariantViewSet(TenantModelViewSet):
    queryset = ProductVariant.objects.select_related("product", "sales_uom").all()
    serializer_class = ProductVariantSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(sku__icontains=search) | Q(name__icontains=search) | Q(barcode__icontains=search)
            )
        product = params.get("product")
        if product:
            queryset = queryset.filter(product_id=product)
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class PriceListViewSet(TenantModelViewSet):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))
        usage = params.get("usage")
        if usage:
            queryset = queryset.filter(usage=usage)
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class PriceListItemViewSet(TenantModelViewSet):
    queryset = PriceListItem.objects.select_related("price_list", "variant").all()
    serializer_class = PriceListItemSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        price_list = params.get("price_list")
        if price_list:
            queryset = queryset.filter(price_list_id=price_list)
        variant = params.get("variant")
        if variant:
            queryset = queryset.filter(variant_id=variant)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(price_list__code__icontains=search)
                | Q(variant__sku__icontains=search)
                | Q(variant__name__icontains=search)
            )
        return queryset


class WarehouseViewSet(TenantModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(description__icontains=search)
            )
        is_default = params.get("is_default")
        if is_default in {"true", "false"}:
            queryset = queryset.filter(is_default=is_default.lower() == "true")
        return queryset


class WarehouseBinViewSet(TenantModelViewSet):
    queryset = WarehouseBin.objects.select_related("warehouse").all()
    serializer_class = WarehouseBinSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        warehouse = params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        bin_type = params.get("bin_type")
        if bin_type:
            queryset = queryset.filter(bin_type=bin_type)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(warehouse__code__icontains=search)
            )
        return queryset


class InventoryBalanceViewSet(TenantModelViewSet):
    queryset = InventoryBalance.objects.select_related("variant", "warehouse").all()
    serializer_class = InventoryBalanceSerializer
    view_permissions = ("inventory.report",)
    http_method_names = ["get", "head", "options"]

    def apply_filters(self, queryset):
        params = self.request.query_params
        variant = params.get("variant")
        if variant:
            queryset = queryset.filter(variant_id=variant)
        warehouse = params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(variant__sku__icontains=search)
                | Q(variant__name__icontains=search)
                | Q(warehouse__code__icontains=search)
                | Q(warehouse__name__icontains=search)
            )
        return queryset


class StockMovementViewSet(TenantModelViewSet):
    queryset = (
        StockMovement.objects.select_related("performed_by")
        .prefetch_related("lines__variant", "lines__warehouse", "ledger_entries")
        .all()
    )
    serializer_class = StockMovementSerializer
    view_permissions = ("inventory.view",)
    edit_permissions = ("inventory.manage",)
    http_method_names = ["get", "post", "head", "options"]

    def apply_filters(self, queryset):
        params = self.request.query_params
        movement_type = params.get("movement_type")
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        reference = params.get("reference")
        if reference:
            queryset = queryset.filter(reference_number__icontains=reference)
        variant = params.get("variant")
        if variant:
            queryset = queryset.filter(lines__variant_id=variant).distinct()
        warehouse = params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(lines__warehouse_id=warehouse).distinct()
        performed_from = params.get("performed_from")
        if performed_from:
            queryset = queryset.filter(performed_at__date__gte=performed_from)
        performed_to = params.get("performed_to")
        if performed_to:
            queryset = queryset.filter(performed_at__date__lte=performed_to)
        return queryset


class InventoryLedgerEntryViewSet(TenantModelViewSet):
    queryset = InventoryLedgerEntry.objects.select_related(
        "movement", "line", "variant", "warehouse"
    ).all()
    serializer_class = InventoryLedgerEntrySerializer
    view_permissions = ("inventory.report",)
    http_method_names = ["get", "head", "options"]

    def apply_filters(self, queryset):
        params = self.request.query_params
        variant = params.get("variant")
        if variant:
            queryset = queryset.filter(variant_id=variant)
        warehouse = params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        movement_type = params.get("movement_type")
        if movement_type:
            queryset = queryset.filter(movement__movement_type=movement_type)
        reference = params.get("reference")
        if reference:
            queryset = queryset.filter(
                Q(reference_id__icontains=reference)
                | Q(reference_type__icontains=reference)
                | Q(movement__reference_number__icontains=reference)
            )
        created_from = params.get("created_from")
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        created_to = params.get("created_to")
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)
        return queryset


class SupplierViewSet(TenantModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    view_permissions = ("purchasing.view",)
    edit_permissions = ("purchasing.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(contact_name__icontains=search)
                | Q(email__icontains=search)
            )
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class PurchaseOrderViewSet(TenantModelViewSet):
    queryset = PurchaseOrder.objects.select_related("supplier", "created_by").prefetch_related("lines__variant")
    serializer_class = PurchaseOrderSerializer
    view_permissions = ("purchasing.view",)
    edit_permissions = ("purchasing.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        supplier = params.get("supplier")
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        order_date_from = params.get("order_date_from")
        if order_date_from:
            queryset = queryset.filter(order_date__gte=order_date_from)
        order_date_to = params.get("order_date_to")
        if order_date_to:
            queryset = queryset.filter(order_date__lte=order_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(supplier__name__icontains=search) | Q(notes__icontains=search)
            )
        return queryset

    def _transition(self, request, order: PurchaseOrder, status: str, audit_code: str) -> response.Response:
        _set_audit_action(request, audit_code)
        order.status = status
        order.save(update_fields=["status", "updated_at"])
        serializer = self.get_serializer(order)
        return response.Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, PurchaseOrder.Status.SUBMITTED, "purchasing.order.submit")

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, PurchaseOrder.Status.APPROVED, "purchasing.order.approve")

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, PurchaseOrder.Status.CANCELLED, "purchasing.order.cancel")

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, PurchaseOrder.Status.CLOSED, "purchasing.order.close")


class PurchaseReceiptViewSet(TenantModelViewSet):
    queryset = PurchaseReceipt.objects.select_related("order", "warehouse", "stock_movement").prefetch_related(
        "lines__variant"
    )
    serializer_class = PurchaseReceiptSerializer
    view_permissions = ("purchasing.view",)
    edit_permissions = ("purchasing.manage",)
    http_method_names = ["get", "post", "patch", "head", "options"]

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        order = params.get("order")
        if order:
            queryset = queryset.filter(order_id=order)
        warehouse = params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        receipt_date_from = params.get("receipt_date_from")
        if receipt_date_from:
            queryset = queryset.filter(receipt_date__gte=receipt_date_from)
        receipt_date_to = params.get("receipt_date_to")
        if receipt_date_to:
            queryset = queryset.filter(receipt_date__lte=receipt_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(number__icontains=search) | Q(notes__icontains=search))
        return queryset

    @action(detail=True, methods=["post"], url_path="post")
    def post_receipt(self, request, pk=None):
        receipt = self.get_object()
        _set_audit_action(request, "purchasing.receipt.post")
        user = request.user if request.user.is_authenticated else None
        PurchasingService.post_receipt(receipt, performed_by=user)
        serializer = self.get_serializer(receipt)
        return response.Response(serializer.data)


class PurchaseBillViewSet(TenantModelViewSet):
    queryset = PurchaseBill.objects.select_related("order").prefetch_related("lines")
    serializer_class = PurchaseBillSerializer
    view_permissions = ("purchasing.view",)
    edit_permissions = ("purchasing.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        order = params.get("order")
        if order:
            queryset = queryset.filter(order_id=order)
        bill_date_from = params.get("bill_date_from")
        if bill_date_from:
            queryset = queryset.filter(bill_date__gte=bill_date_from)
        bill_date_to = params.get("bill_date_to")
        if bill_date_to:
            queryset = queryset.filter(bill_date__lte=bill_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(number__icontains=search) | Q(notes__icontains=search))
        return queryset

    @action(detail=True, methods=["post"], url_path="post")
    def post_bill(self, request, pk=None):
        bill = self.get_object()
        _set_audit_action(request, "purchasing.bill.post")
        PurchasingService.post_bill(bill)
        serializer = self.get_serializer(bill)
        return response.Response(serializer.data)


class PurchasePaymentViewSet(TenantModelViewSet):
    queryset = PurchasePayment.objects.select_related("bill").all()
    serializer_class = PurchasePaymentSerializer
    view_permissions = ("purchasing.view",)
    edit_permissions = ("purchasing.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        bill = params.get("bill")
        if bill:
            queryset = queryset.filter(bill_id=bill)
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        payment_date_from = params.get("payment_date_from")
        if payment_date_from:
            queryset = queryset.filter(payment_date__gte=payment_date_from)
        payment_date_to = params.get("payment_date_to")
        if payment_date_to:
            queryset = queryset.filter(payment_date__lte=payment_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(reference__icontains=search) | Q(notes__icontains=search)
            )
        return queryset

    @action(detail=True, methods=["post"], url_path="void")
    def void(self, request, pk=None):
        payment = self.get_object()
        _set_audit_action(request, "purchasing.payment.void")
        payment.status = PurchasePayment.Status.VOID
        payment.save(update_fields=["status", "updated_at"])
        PurchasingService.post_payment(payment)
        serializer = self.get_serializer(payment)
        return response.Response(serializer.data)


class SalesOrderViewSet(TenantModelViewSet):
    queryset = SalesOrder.objects.select_related("customer", "created_by").prefetch_related("lines__variant")
    serializer_class = SalesOrderSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        customer = params.get("customer")
        if customer:
            queryset = queryset.filter(customer_id=customer)
        order_date_from = params.get("order_date_from")
        if order_date_from:
            queryset = queryset.filter(order_date__gte=order_date_from)
        order_date_to = params.get("order_date_to")
        if order_date_to:
            queryset = queryset.filter(order_date__lte=order_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(customer__name__icontains=search) | Q(notes__icontains=search)
            )
        return queryset

    def _transition(self, request, order: SalesOrder, status: str, audit_code: str) -> response.Response:
        _set_audit_action(request, audit_code)
        order.status = status
        order.save(update_fields=["status", "updated_at"])
        serializer = self.get_serializer(order)
        return response.Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, SalesOrder.Status.CONFIRMED, "sales.order.confirm")

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, SalesOrder.Status.CANCELLED, "sales.order.cancel")

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        order = self.get_object()
        return self._transition(request, order, SalesOrder.Status.CLOSED, "sales.order.close")


class DeliveryNoteViewSet(TenantModelViewSet):
    queryset = DeliveryNote.objects.select_related("order", "warehouse", "stock_movement").prefetch_related(
        "lines__variant"
    )
    serializer_class = DeliveryNoteSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)
    http_method_names = ["get", "post", "patch", "head", "options"]

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        order = params.get("order")
        if order:
            queryset = queryset.filter(order_id=order)
        warehouse = params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)
        delivery_date_from = params.get("delivery_date_from")
        if delivery_date_from:
            queryset = queryset.filter(delivery_date__gte=delivery_date_from)
        delivery_date_to = params.get("delivery_date_to")
        if delivery_date_to:
            queryset = queryset.filter(delivery_date__lte=delivery_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(number__icontains=search) | Q(notes__icontains=search))
        return queryset

    @action(detail=True, methods=["post"], url_path="post")
    def post_delivery(self, request, pk=None):
        delivery = self.get_object()
        _set_audit_action(request, "sales.delivery.post")
        performer = request.user if request.user.is_authenticated else None
        SalesService.post_delivery(delivery, performed_by=performer)
        serializer = self.get_serializer(delivery)
        return response.Response(serializer.data)


class SalesInvoiceViewSet(TenantModelViewSet):
    queryset = SalesInvoice.objects.select_related("order").prefetch_related("lines")
    serializer_class = SalesInvoiceSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        order = params.get("order")
        if order:
            queryset = queryset.filter(order_id=order)
        invoice_date_from = params.get("invoice_date_from")
        if invoice_date_from:
            queryset = queryset.filter(invoice_date__gte=invoice_date_from)
        invoice_date_to = params.get("invoice_date_to")
        if invoice_date_to:
            queryset = queryset.filter(invoice_date__lte=invoice_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(Q(number__icontains=search) | Q(notes__icontains=search))
        return queryset

    @action(detail=True, methods=["post"], url_path="post")
    def post_invoice(self, request, pk=None):
        invoice = self.get_object()
        _set_audit_action(request, "sales.invoice.post")
        SalesService.post_invoice(invoice)
        serializer = self.get_serializer(invoice)
        return response.Response(serializer.data)


class SalesPaymentViewSet(TenantModelViewSet):
    queryset = SalesPayment.objects.select_related("invoice").all()
    serializer_class = SalesPaymentSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        invoice = params.get("invoice")
        if invoice:
            queryset = queryset.filter(invoice_id=invoice)
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        payment_date_from = params.get("payment_date_from")
        if payment_date_from:
            queryset = queryset.filter(payment_date__gte=payment_date_from)
        payment_date_to = params.get("payment_date_to")
        if payment_date_to:
            queryset = queryset.filter(payment_date__lte=payment_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(reference__icontains=search) | Q(notes__icontains=search)
            )
        return queryset

    @action(detail=True, methods=["post"], url_path="void")
    def void(self, request, pk=None):
        payment = self.get_object()
        _set_audit_action(request, "sales.payment.void")
        payment.status = SalesPayment.Status.VOID
        payment.save(update_fields=["status", "updated_at"])
        SalesService.post_payment(payment)
        serializer = self.get_serializer(payment)
        return response.Response(serializer.data)


class SalesRefundViewSet(TenantModelViewSet):
    queryset = SalesRefund.objects.select_related("invoice").all()
    serializer_class = SalesRefundSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        invoice = params.get("invoice")
        if invoice:
            queryset = queryset.filter(invoice_id=invoice)
        refund_date_from = params.get("refund_date_from")
        if refund_date_from:
            queryset = queryset.filter(refund_date__gte=refund_date_from)
        refund_date_to = params.get("refund_date_to")
        if refund_date_to:
            queryset = queryset.filter(refund_date__lte=refund_date_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(reason__icontains=search) | Q(notes__icontains=search)
            )
        return queryset


class MenuViewSet(TenantModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(name__icontains=search)
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class MenuSectionViewSet(TenantModelViewSet):
    queryset = MenuSection.objects.select_related("menu").all()
    serializer_class = MenuSectionSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        menu = params.get("menu")
        if menu:
            queryset = queryset.filter(menu_id=menu)
        search = params.get("q")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class MenuItemViewSet(TenantModelViewSet):
    queryset = MenuItem.objects.select_related("section", "section__menu", "variant").all()
    serializer_class = MenuItemSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        section = params.get("section")
        if section:
            queryset = queryset.filter(section_id=section)
        menu = params.get("menu")
        if menu:
            queryset = queryset.filter(section__menu_id=menu)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(sku__icontains=search)
            )
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class MenuModifierGroupViewSet(TenantModelViewSet):
    queryset = MenuModifierGroup.objects.select_related("item", "item__section").all()
    serializer_class = MenuModifierGroupSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        item = params.get("item")
        if item:
            queryset = queryset.filter(item_id=item)
        return queryset


class MenuModifierOptionViewSet(TenantModelViewSet):
    queryset = MenuModifierOption.objects.select_related("group", "group__item").all()
    serializer_class = MenuModifierOptionSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        group = params.get("group")
        if group:
            queryset = queryset.filter(group_id=group)
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class RecipeViewSet(TenantModelViewSet):
    queryset = Recipe.objects.select_related("item").prefetch_related("components").all()
    serializer_class = RecipeSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        item = params.get("item")
        if item:
            queryset = queryset.filter(item_id=item)
        return queryset


class RecipeComponentViewSet(TenantModelViewSet):
    queryset = RecipeComponent.objects.select_related("recipe", "ingredient").all()
    serializer_class = RecipeComponentSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        recipe = params.get("recipe")
        if recipe:
            queryset = queryset.filter(recipe_id=recipe)
        ingredient = params.get("ingredient")
        if ingredient:
            queryset = queryset.filter(ingredient_id=ingredient)
        return queryset


class KitchenDisplayEventViewSet(TenantModelViewSet):
    queryset = KitchenDisplayEvent.objects.select_related("ticket").all()
    serializer_class = KitchenDisplayEventSerializer
    view_permissions = ("restaurant.view",)
    http_method_names = ["get", "head", "options"]

    def apply_filters(self, queryset):
        params = self.request.query_params
        ticket = params.get("ticket")
        if ticket:
            queryset = queryset.filter(ticket_id=ticket)
        return queryset


class KitchenOrderTicketViewSet(TenantModelViewSet):
    queryset = KitchenOrderTicket.objects.prefetch_related("lines__item", "kds_events").all()
    serializer_class = KitchenOrderTicketSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status_value = params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        source = params.get("source")
        if source:
            queryset = queryset.filter(source=source)
        table = params.get("table")
        if table:
            queryset = queryset.filter(table_number__iexact=table)
        since = params.get("placed_from")
        if since:
            queryset = queryset.filter(placed_at__date__gte=since)
        until = params.get("placed_to")
        if until:
            queryset = queryset.filter(placed_at__date__lte=until)
        return queryset

    @action(detail=True, methods=["post"], url_path="kds")
    def kds_action(self, request, pk=None):
        ticket = self.get_object()
        serializer = KitchenDisplayActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        actor = serializer.validated_data.get("actor", "")
        if action == KitchenDisplayEvent.Action.BUMP:
            ticket.mark_ready()
        elif action == KitchenDisplayEvent.Action.RECALL:
            ticket.status = KitchenOrderTicket.Status.IN_PROGRESS
            ticket.save(update_fields=["status", "updated_at"])

        event = RestaurantService.publish_kds_event(
            tenant=self.request.tenant,
            ticket=ticket,
            action=action,
            actor=actor,
        )
        payload = KitchenDisplayEventSerializer(event, context=self.get_serializer_context()).data
        return response.Response(payload, status=status.HTTP_200_OK)


class QROrderingTokenViewSet(TenantModelViewSet):
    queryset = QROrderingToken.objects.select_related("menu").all()
    serializer_class = QROrderingTokenSerializer
    view_permissions = ("restaurant.view",)
    edit_permissions = ("restaurant.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        menu = params.get("menu")
        if menu:
            queryset = queryset.filter(menu_id=menu)
        active = params.get("is_active")
        if active in {"true", "false"}:
            queryset = queryset.filter(is_active=active.lower() == "true")
        table = params.get("table")
        if table:
            queryset = queryset.filter(table_number__iexact=table)
        return queryset

    @action(detail=True, methods=["get"], url_path="verify")
    def verify(self, request, pk=None):
        token = self.get_object()
        is_valid = RestaurantService.verify_qr_token(token)
        return response.Response({"valid": is_valid})


class POSShiftViewSet(TenantModelViewSet):
    queryset = POSShift.objects.select_related("opened_by", "closed_by").all()
    serializer_class = POSShiftSerializer
    view_permissions = ("pos.view",)
    edit_permissions = ("pos.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        register = params.get("register")
        if register:
            queryset = queryset.filter(register_code__iexact=register)
        opened_from = params.get("opened_from")
        if opened_from:
            queryset = queryset.filter(opened_at__date__gte=opened_from)
        opened_to = params.get("opened_to")
        if opened_to:
            queryset = queryset.filter(opened_at__date__lte=opened_to)
        return queryset

    @action(detail=True, methods=["post"], url_path="close")
    def close_shift(self, request, pk=None):
        shift = self.get_object()
        _set_audit_action(request, "pos.shift.close")
        user = request.user if request.user.is_authenticated else None
        closing_float = request.data.get("closing_float")
        if closing_float is not None:
            try:
                closing_float = Decimal(str(closing_float))
            except Exception as exc:  # pragma: no cover - defensive
                raise exceptions.ValidationError({"closing_float": "Provide a numeric value."}) from exc
        POSService.close_shift(shift, closed_by=user, closing_float=closing_float)
        serializer = self.get_serializer(shift)
        return response.Response(serializer.data)


class POSSaleViewSet(TenantModelViewSet):
    queryset = (
        POSSale.objects.select_related("shift", "customer", "warehouse")
        .prefetch_related("items__variant", "payments")
        .all()
    )
    serializer_class = POSSaleSerializer
    view_permissions = ("pos.view",)
    edit_permissions = ("pos.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        shift = params.get("shift")
        if shift:
            queryset = queryset.filter(shift_id=shift)
        register = params.get("register")
        if register:
            queryset = queryset.filter(shift__register_code__iexact=register)
        created_from = params.get("created_from")
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        created_to = params.get("created_to")
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search)
                | Q(notes__icontains=search)
                | Q(customer__name__icontains=search)
            )
        return queryset

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        sale = self.get_object()
        _set_audit_action(request, "pos.sale.finalize")
        performer = request.user if request.user.is_authenticated else None
        POSService.finalize_sale(sale, performed_by=performer)
        serializer = self.get_serializer(sale)
        return response.Response(serializer.data)


class POSReceiptViewSet(TenantModelViewSet):
    queryset = POSReceipt.objects.select_related("sale").all()
    serializer_class = POSReceiptSerializer
    view_permissions = ("pos.view",)
    edit_permissions = ("pos.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        sale = params.get("sale")
        if sale:
            queryset = queryset.filter(sale_id=sale)
        number = params.get("number")
        if number:
            queryset = queryset.filter(number__icontains=number)
        return queryset


class POSOfflineQueueViewSet(TenantModelViewSet):
    queryset = POSOfflineQueueItem.objects.all()
    serializer_class = POSOfflineQueueItemSerializer
    view_permissions = ("pos.view",)
    edit_permissions = ("pos.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        operation = params.get("operation")
        if operation:
            queryset = queryset.filter(operation__iexact=operation)
        return queryset

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request, pk=None):
        queue_item = self.get_object()
        _set_audit_action(request, "pos.offline.sync")
        error = request.data.get("error_message")
        POSService.mark_offline_item_synced(queue_item, error=error)
        serializer = self.get_serializer(queue_item)
        return response.Response(serializer.data)


class CustomerViewSet(TenantModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    view_permissions = ("sales.view",)
    edit_permissions = ("sales.manage",)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )
        is_active = params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class InventorySummaryReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasTenantPermissions]
    required_permissions = ("reports.view",)

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise exceptions.ValidationError({"detail": "Provide the X-Tenant header to request reports."})

        warehouse_rows = (
            InventoryBalance.objects.filter(tenant=tenant)
            .values("warehouse__code", "warehouse__name")
            .annotate(
                quantity=Sum("on_hand"),
                value=Sum(F("on_hand") * F("average_cost")),
            )
        )

        variant_totals: dict[str, dict[str, Decimal | str]] = {}
        for sku, name, qty, avg_cost in InventoryBalance.objects.filter(tenant=tenant).values_list(
            "variant__sku",
            "variant__name",
            "on_hand",
            "average_cost",
        ):
            entry = variant_totals.setdefault(
                sku,
                {
                    "variantSku": sku,
                    "variantName": name,
                    "quantity": Decimal("0"),
                    "value": Decimal("0"),
                },
            )
            entry["quantity"] += qty
            entry["value"] += qty * avg_cost

        variant_summary = []
        for data in variant_totals.values():
            quantity = data["quantity"]
            value = data["value"]
            average_cost = Decimal("0")
            if quantity:
                average_cost = (value / quantity).quantize(DECIMAL_PRECISION_CURRENCY)
            variant_summary.append(
                {
                    "variantSku": data["variantSku"],
                    "variantName": data["variantName"],
                    "onHand": quantity,
                    "inventoryValue": value.quantize(DECIMAL_PRECISION_CURRENCY),
                    "averageCost": average_cost,
                }
            )

        response_payload = {
            "warehouses": [
                {
                    "warehouseCode": row["warehouse__code"],
                    "warehouseName": row["warehouse__name"],
                    "onHand": row["quantity"] or Decimal("0"),
                    "inventoryValue": (row["value"] or Decimal("0")).quantize(DECIMAL_PRECISION_CURRENCY),
                }
                for row in warehouse_rows
            ],
            "variants": sorted(variant_summary, key=lambda item: item["variantSku"]),
            "generatedAt": timezone.now(),
        }
        return response.Response(response_payload)


class PurchasingPipelineReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasTenantPermissions]
    required_permissions = ("reports.view",)

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise exceptions.ValidationError({"detail": "Provide the X-Tenant header to request reports."})

        orders = list(
            PurchaseOrder.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"), total=Sum("total_amount"))
        )
        receipts = list(
            PurchaseReceipt.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"))
        )
        bills = list(
            PurchaseBill.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"), total=Sum("total_amount"))
        )
        payments = list(
            PurchasePayment.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"), total=Sum("amount"))
        )

        outstanding_orders = (
            PurchaseOrder.objects.filter(
                tenant=tenant, status__in=[PurchaseOrder.Status.SUBMITTED, PurchaseOrder.Status.RECEIVING]
            ).aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0")
        )

        payload = {
            "orders": orders,
            "receipts": receipts,
            "bills": bills,
            "payments": payments,
            "outstandingAmount": outstanding_orders.quantize(DECIMAL_PRECISION_CURRENCY),
            "generatedAt": timezone.now(),
        }
        return response.Response(payload)


class SalesPipelineReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasTenantPermissions]
    required_permissions = ("reports.view",)

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise exceptions.ValidationError({"detail": "Provide the X-Tenant header to request reports."})

        orders = list(
            SalesOrder.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"), total=Sum("total_amount"))
        )
        deliveries = list(
            DeliveryNote.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"))
        )
        invoices = list(
            SalesInvoice.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"), total=Sum("total_amount"))
        )
        payments = list(
            SalesPayment.objects.filter(tenant=tenant)
            .values("status")
            .annotate(count=Count("id"), total=Sum("amount"))
        )

        outstanding_invoices = (
            SalesInvoice.objects.filter(
                tenant=tenant, status__in=[SalesInvoice.Status.POSTED]
            ).aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0")
        )

        payload = {
            "orders": orders,
            "deliveries": deliveries,
            "invoices": invoices,
            "payments": payments,
            "outstandingAmount": outstanding_invoices.quantize(DECIMAL_PRECISION_CURRENCY),
            "generatedAt": timezone.now(),
        }
        return response.Response(payload)





from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone

from api.models import (
    Customer,
    DeliveryNote,
    DeliveryNoteLine,
    POSShift,
    POSSale,
    POSSaleItem,
    POSSalePayment,
    Product,
    ProductCategory,
    ProductVariant,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
    SalesInvoice,
    SalesInvoiceLine,
    SalesOrder,
    SalesOrderLine,
    Supplier,
    Tenant,
    UnitOfMeasure,
    Warehouse,
    Menu,
    MenuSection,
    MenuItem,
    Recipe,
    RecipeComponent,
    KitchenOrderTicket,
    KitchenOrderLine,
    KitchenDisplayEvent,
    QROrderingToken,
)
from api.services.inventory import InventoryService, StockMovementLineParams
from api.services.pos import POSService
from api.services.purchasing import PurchasingService
from api.services.sales import SalesService
from api.services.restaurant import RestaurantService


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name="TestCo", slug="testco", timezone="UTC")


@pytest.fixture
def base_objects(tenant):
    uom = UnitOfMeasure.objects.create(tenant=tenant, code="EA", name="Each")
    category = ProductCategory.objects.create(tenant=tenant, code="DEFAULT", name="Default")
    product = Product.objects.create(
        tenant=tenant,
        code="PROD-001",
        name="Test Widget",
        category=category,
        base_uom=uom,
    )
    variant = ProductVariant.objects.create(
        tenant=tenant,
        product=product,
        sku="PROD-001",
        name="Test Widget",
        sales_uom=uom,
        conversion_factor=Decimal("1"),
    )
    warehouse = Warehouse.objects.create(tenant=tenant, code="MAIN", name="Main Warehouse")
    supplier = Supplier.objects.create(tenant=tenant, code="SUP", name="Supplier One")
    customer = Customer.objects.create(tenant=tenant, code="CUST", name="Customer One")
    return {
        "uom": uom,
        "variant": variant,
        "warehouse": warehouse,
        "supplier": supplier,
        "customer": customer,
    }


@pytest.mark.django_db
def test_inventory_weighted_average(tenant, base_objects):
    variant = base_objects["variant"]
    warehouse = base_objects["warehouse"]

    InventoryService.record_movement(
        tenant=tenant,
        movement_type="purchase_receipt",
        lines=[
            StockMovementLineParams(
                variant=variant,
                warehouse=warehouse,
                quantity=Decimal("10"),
                unit_cost=Decimal("5"),
            )
        ],
        reference_number="GRN-1",
    )
    balance = variant.inventory_balances.get(warehouse=warehouse)
    assert balance.on_hand == Decimal("10")
    assert balance.average_cost == Decimal("5")

    InventoryService.record_movement(
        tenant=tenant,
        movement_type="purchase_receipt",
        lines=[
            StockMovementLineParams(
                variant=variant,
                warehouse=warehouse,
                quantity=Decimal("10"),
                unit_cost=Decimal("7"),
            )
        ],
        reference_number="GRN-2",
    )
    balance.refresh_from_db()
    assert balance.on_hand == Decimal("20")
    assert balance.average_cost == Decimal("6")

    InventoryService.record_movement(
        tenant=tenant,
        movement_type="sale_shipment",
        lines=[
            StockMovementLineParams(
                variant=variant,
                warehouse=warehouse,
                quantity=Decimal("-4"),
            )
        ],
        reference_number="SO-1",
    )
    balance.refresh_from_db()
    assert balance.on_hand == Decimal("16")
    assert balance.average_cost == Decimal("6")


@pytest.mark.django_db
def test_purchasing_receipt_updates_order_and_inventory(tenant, base_objects):
    variant = base_objects["variant"]
    warehouse = base_objects["warehouse"]
    supplier = base_objects["supplier"]

    order = PurchaseOrder.objects.create(
        tenant=tenant,
        number="PO-1",
        supplier=supplier,
        order_date=timezone.now().date(),
    )
    line = PurchaseOrderLine.objects.create(
        tenant=tenant,
        order=order,
        variant=variant,
        ordered_quantity=Decimal("5"),
        unit_price=Decimal("4"),
    )
    receipt = PurchaseReceipt.objects.create(
        tenant=tenant,
        order=order,
        number="GRN-PO-1",
        warehouse=warehouse,
    )
    PurchaseReceiptLine.objects.create(
        tenant=tenant,
        receipt=receipt,
        order_line=line,
        variant=variant,
        quantity=Decimal("5"),
        unit_cost=Decimal("4"),
    )

    PurchasingService.post_receipt(receipt)
    line.refresh_from_db()
    order.refresh_from_db()
    assert line.received_quantity == Decimal("5")
    assert order.status in {PurchaseOrder.Status.RECEIVING, PurchaseOrder.Status.RECEIVED}
    balance = variant.inventory_balances.get(warehouse=warehouse)
    assert balance.on_hand == Decimal("5")


@pytest.mark.django_db
def test_sales_delivery_and_invoice_flow(tenant, base_objects):
    variant = base_objects["variant"]
    warehouse = base_objects["warehouse"]
    supplier = base_objects["supplier"]
    customer = base_objects["customer"]

    # seed stock
    InventoryService.record_movement(
        tenant=tenant,
        movement_type="purchase_receipt",
        lines=[
            StockMovementLineParams(
                variant=variant,
                warehouse=warehouse,
                quantity=Decimal("8"),
                unit_cost=Decimal("5"),
            )
        ],
        reference_number="GRN-SEED",
    )

    order = SalesOrder.objects.create(
        tenant=tenant,
        number="SO-1",
        customer=customer,
        order_date=timezone.now().date(),
    )
    order_line = SalesOrderLine.objects.create(
        tenant=tenant,
        order=order,
        variant=variant,
        ordered_quantity=Decimal("3"),
        unit_price=Decimal("9"),
    )
    delivery = DeliveryNote.objects.create(
        tenant=tenant,
        order=order,
        number="DN-1",
        warehouse=warehouse,
    )
    DeliveryNoteLine.objects.create(
        tenant=tenant,
        delivery=delivery,
        order_line=order_line,
        variant=variant,
        quantity=Decimal("3"),
    )
    SalesService.post_delivery(delivery)
    order_line.refresh_from_db()
    assert order_line.delivered_quantity == Decimal("3")

    invoice = SalesInvoice.objects.create(
        tenant=tenant,
        order=order,
        number="INV-1",
    )
    SalesInvoiceLine.objects.create(
        tenant=tenant,
        invoice=invoice,
        order_line=order_line,
        description="Widget",
        quantity=Decimal("3"),
        unit_price=Decimal("9"),
    )
    SalesService.post_invoice(invoice)
    invoice.refresh_from_db()
    assert invoice.total_amount == Decimal("27")
    order_line.refresh_from_db()
    assert order_line.invoiced_quantity == Decimal("3")


@pytest.mark.django_db
def test_pos_sale_finalize(tenant, base_objects):
    variant = base_objects["variant"]
    warehouse = base_objects["warehouse"]

    InventoryService.record_movement(
        tenant=tenant,
        movement_type="purchase_receipt",
        lines=[
            StockMovementLineParams(
                variant=variant,
                warehouse=warehouse,
                quantity=Decimal("6"),
                unit_cost=Decimal("4"),
            )
        ],
        reference_number="GRN-POS",
    )

    shift = POSShift.objects.create(tenant=tenant, register_code="REG-1")
    sale = POSSale.objects.create(
        tenant=tenant,
        shift=shift,
        warehouse=warehouse,
        reference="POS-1",
    )
    POSSaleItem.objects.create(
        tenant=tenant,
        sale=sale,
        variant=variant,
        quantity=Decimal("2"),
        unit_price=Decimal("8"),
    )
    POSSalePayment.objects.create(
        tenant=tenant,
        sale=sale,
        method="cash",
        amount=Decimal("16"),
    )

    POSService.recalculate_sale_totals(sale)
    POSService.finalize_sale(sale)
    sale.refresh_from_db()
    assert sale.status == POSSale.Status.PAID
    assert sale.stock_movement is not None
    balance = variant.inventory_balances.get(warehouse=warehouse)
    assert balance.on_hand == Decimal("4")




@pytest.mark.django_db
def test_recipe_consumption_reduces_balance(tenant, base_objects):
    variant = base_objects["variant"]
    warehouse = base_objects["warehouse"]
    uom = base_objects["uom"]

    InventoryService.record_movement(
        tenant=tenant,
        movement_type="purchase_receipt",
        lines=[
            StockMovementLineParams(
                variant=variant,
                warehouse=warehouse,
                quantity=Decimal("10"),
                unit_cost=Decimal("3"),
            )
        ],
        reference_number="GRN-RECIPE",
    )

    menu = Menu.objects.create(tenant=tenant, name="Dinner")
    section = MenuSection.objects.create(tenant=tenant, menu=menu, name="Entrees")
    item = MenuItem.objects.create(
        tenant=tenant,
        section=section,
        name="Pasta",
        base_price=Decimal("12"),
    )
    recipe = Recipe.objects.create(
        tenant=tenant,
        item=item,
        instructions="Boil and serve",
        yield_quantity=Decimal("1"),
        yield_uom=uom,
    )
    RecipeComponent.objects.create(
        tenant=tenant,
        recipe=recipe,
        ingredient=variant,
        quantity=Decimal("0.5"),
        uom=uom,
    )

    ticket = KitchenOrderTicket.objects.create(
        tenant=tenant,
        ticket_number="KOT-1",
        table_number="T1",
        source=KitchenOrderTicket.Source.DINE_IN,
    )

    RestaurantService.create_ticket(
        tenant=tenant,
        ticket=ticket,
        lines=[{"item": item, "quantity": Decimal("2") }],
    )

    balance = variant.inventory_balances.get(warehouse=warehouse)
    assert balance.on_hand == Decimal("9")  # consumed 1 unit total


@pytest.mark.django_db
def test_kds_bump_creates_event(tenant, base_objects):
    uom = base_objects["uom"]
    variant = base_objects["variant"]
    warehouse = base_objects["warehouse"]

    menu = Menu.objects.create(tenant=tenant, name="Lunch")
    section = MenuSection.objects.create(tenant=tenant, menu=menu, name="Main")
    item = MenuItem.objects.create(
        tenant=tenant,
        section=section,
        name="Burger",
        base_price=Decimal("9"),
    )
    recipe = Recipe.objects.create(tenant=tenant, item=item, yield_quantity=Decimal("1"), yield_uom=uom)
    RecipeComponent.objects.create(
        tenant=tenant,
        recipe=recipe,
        ingredient=variant,
        quantity=Decimal("1"),
        uom=uom,
    )

    ticket = KitchenOrderTicket.objects.create(
        tenant=tenant,
        ticket_number="KOT-2",
        source=KitchenOrderTicket.Source.TAKEAWAY,
    )
    RestaurantService.create_ticket(
        tenant=tenant,
        ticket=ticket,
        lines=[{"item": item, "quantity": Decimal("1") }],
    )

    event = RestaurantService.publish_kds_event(
        tenant=tenant,
        ticket=ticket,
        action=KitchenDisplayEvent.Action.BUMP,
        actor="chef",
    )
    assert event.action == KitchenDisplayEvent.Action.BUMP
    assert event.actor == "chef"


@pytest.mark.django_db
def test_qr_token_validation(tenant):
    menu = Menu.objects.create(tenant=tenant, name="Snacks")
    token = QROrderingToken.objects.create(
        tenant=tenant,
        token="abc123",
        menu=menu,
        table_number="T5",
        expires_at=timezone.now() + timezone.timedelta(hours=1),
    )
    assert RestaurantService.verify_qr_token(token) is True
    token.is_active = False
    token.save(update_fields=["is_active"])
    assert RestaurantService.verify_qr_token(token) is False


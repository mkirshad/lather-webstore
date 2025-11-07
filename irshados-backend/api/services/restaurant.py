from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from ..models import (
    KitchenDisplayEvent,
    KitchenOrderLine,
    KitchenOrderTicket,
    MenuItem,
    MenuModifierOption,
    MenuModifierGroup,
    QROrderingToken,
    RecipeComponent,
    StockMovement,
    Tenant,
    Warehouse,
)
from .inventory import InventoryService, StockMovementLineParams


class RestaurantService:
    """Utility helpers for restaurant operations."""

    @staticmethod
    @transaction.atomic
    def create_ticket(
        *,
        tenant: Tenant,
        ticket: KitchenOrderTicket,
        lines: Iterable[dict],
        performed_by=None,
    ) -> KitchenOrderTicket:
        created_lines: list[KitchenOrderLine] = []
        for line in lines:
            item: MenuItem = line["item"]
            quantity: Decimal = Decimal(line.get("quantity", 1))
            modifiers = line.get("modifiers", [])
            kot_line = KitchenOrderLine.objects.create(
                tenant=tenant,
                ticket=ticket,
                item=item,
                quantity=quantity,
                modifiers=modifiers,
                notes=line.get("notes", ""),
            )
            created_lines.append(kot_line)
            RestaurantService._consume_recipe(tenant=tenant, item=item, quantity=quantity)

        if performed_by:
            KitchenDisplayEvent.objects.create(
                tenant=tenant,
                ticket=ticket,
                action=KitchenDisplayEvent.Action.RECALL,
                actor=str(performed_by),
                metadata={"system": "create"},
            )
        return ticket

    @staticmethod
    def _consume_recipe(*, tenant: Tenant, item: MenuItem, quantity: Decimal) -> None:
        recipe = getattr(item, "recipe", None)
        if recipe is None:
            return
        if recipe.yield_quantity == 0:
            yield_qty = Decimal("1")
        else:
            yield_qty = recipe.yield_quantity
        factor = quantity / yield_qty
        lines: list[StockMovementLineParams] = []
        components = recipe.components.select_related("ingredient", "uom")
        warehouse = RestaurantService._resolve_warehouse(tenant)
        for component in components:
            consume_qty = Decimal(component.quantity) * factor
            lines.append(
                StockMovementLineParams(
                    variant=component.ingredient,
                    warehouse=warehouse,
                    quantity=consume_qty * Decimal("-1"),
                    unit_cost=None,
                    metadata={"recipe": recipe.item.name},
                )
            )
        valid_lines = [params for params in lines if params.warehouse is not None]
        if not valid_lines:
            return
        InventoryService.record_movement(
            tenant=tenant,
            movement_type=StockMovement.MovementType.SALE_SHIPMENT,
            lines=valid_lines,
            reference_number=f"RECIPE-{ticket_reference()}",
            description=f"Recipe consumption for {item.name}",
        )

    @staticmethod
    def publish_kds_event(*, tenant: Tenant, ticket: KitchenOrderTicket, action: str, actor: str = "") -> KitchenDisplayEvent:
        event = KitchenDisplayEvent.objects.create(
            tenant=tenant,
            ticket=ticket,
            action=action,
            actor=actor,
        )
        return event

    @staticmethod
    def verify_qr_token(token: QROrderingToken) -> bool:
        if not token.is_active:
            return False
        if token.expires_at and timezone.now() >= token.expires_at:
            return False
        return True

    @staticmethod
    def _resolve_warehouse(tenant: Tenant):
        warehouse = Warehouse.objects.filter(tenant=tenant, is_default=True).first()
        if warehouse is None:
            warehouse = Warehouse.objects.filter(tenant=tenant).first()
        return warehouse


def ticket_reference() -> str:
    return timezone.now().strftime("%Y%m%d%H%M%S%f")






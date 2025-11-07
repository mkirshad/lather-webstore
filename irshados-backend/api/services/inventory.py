from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from django.db import transaction
from django.utils import timezone

from ..models import (
    InventoryBalance,
    InventoryLedgerEntry,
    ProductVariant,
    StockMovement,
    StockMovementLine,
    Tenant,
    Warehouse,
)


DECIMAL_PRECISION_QUANTITY = Decimal("0.001")
DECIMAL_PRECISION_CURRENCY = Decimal("0.0001")


def _quantize(value: Decimal, *, precision: Decimal) -> Decimal:
    return value.quantize(precision, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class StockMovementLineParams:
    variant: ProductVariant
    warehouse: Warehouse
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    metadata: Optional[dict] = None
    reference_type: str = ""
    reference_id: str = ""
    note: str = ""

    def normalized_quantity(self) -> Decimal:
        return _quantize(Decimal(self.quantity), precision=DECIMAL_PRECISION_QUANTITY)

    def normalized_unit_cost(self) -> Decimal:
        if self.unit_cost is None:
            return Decimal("0")
        return _quantize(Decimal(self.unit_cost), precision=DECIMAL_PRECISION_CURRENCY)


class InventoryService:
    """Utility helpers for inventory movements with weighted average costing."""

    @staticmethod
    @transaction.atomic
    def record_movement(
        *,
        tenant: Tenant,
        movement_type: str,
        lines: Iterable[StockMovementLineParams],
        reference_number: str | None = None,
        description: str = "",
        performed_by=None,
        source_document_type: str = "",
        source_document_id: str = "",
        metadata: Optional[dict] = None,
    ) -> StockMovement:
        movement = StockMovement.objects.create(
            tenant=tenant,
            movement_type=movement_type,
            reference_number=reference_number or "",
            description=description,
            performed_by=performed_by,
            source_document_type=source_document_type,
            source_document_id=source_document_id,
            metadata=metadata or {},
            performed_at=timezone.now(),
        )

        for line_params in lines:
            InventoryService._process_line(movement=movement, params=line_params)

        return movement

    @staticmethod
    def _process_line(*, movement: StockMovement, params: StockMovementLineParams) -> None:
        tenant = movement.tenant
        variant = params.variant
        warehouse = params.warehouse
        quantity_delta = params.normalized_quantity()

        balance, _ = (
            InventoryBalance.objects.select_for_update()
            .get_or_create(
                tenant=tenant,
                variant=variant,
                warehouse=warehouse,
                defaults={
                    "on_hand": Decimal("0"),
                    "allocated": Decimal("0"),
                    "on_order": Decimal("0"),
                    "average_cost": Decimal("0"),
                },
            )
        )

        previous_quantity = balance.on_hand
        previous_avg_cost = balance.average_cost
        previous_value = previous_quantity * previous_avg_cost

        unit_cost = params.normalized_unit_cost()
        if quantity_delta < 0 and (unit_cost == 0):
            unit_cost = previous_avg_cost

        value_delta = _quantize(unit_cost * quantity_delta, precision=DECIMAL_PRECISION_CURRENCY)

        new_quantity = previous_quantity + quantity_delta
        new_value = previous_value + value_delta
        new_value = _quantize(new_value, precision=DECIMAL_PRECISION_CURRENCY)

        if new_quantity == 0:
            average_cost = Decimal("0")
            new_value = Decimal("0")
        else:
            average_cost = _quantize(new_value / new_quantity, precision=DECIMAL_PRECISION_CURRENCY)

        balance.on_hand = _quantize(new_quantity, precision=DECIMAL_PRECISION_QUANTITY)
        balance.average_cost = average_cost
        balance.last_movement_at = movement.performed_at
        balance.save(update_fields=["on_hand", "average_cost", "last_movement_at", "updated_at"])

        line = StockMovementLine.objects.create(
            tenant=tenant,
            movement=movement,
            variant=variant,
            warehouse=warehouse,
            quantity=quantity_delta,
            unit_cost=unit_cost,
            value_delta=value_delta,
            metadata=params.metadata or {},
        )

        InventoryLedgerEntry.objects.create(
            tenant=tenant,
            movement=movement,
            line=line,
            variant=variant,
            warehouse=warehouse,
            quantity_delta=quantity_delta,
            value_delta=value_delta,
            running_quantity=balance.on_hand,
            running_value=new_value,
            average_cost=average_cost,
            reference_type=params.reference_type,
            reference_id=params.reference_id,
            note=params.note,
        )

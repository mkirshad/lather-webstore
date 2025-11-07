from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from ..models import (
    POSOfflineQueueItem,
    POSSale,
    POSSaleItem,
    POSSalePayment,
    POSShift,
    StockMovement,
)
from .inventory import InventoryService, StockMovementLineParams, DECIMAL_PRECISION_CURRENCY


def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_PRECISION_CURRENCY)


class POSService:
    """Helper utilities for POS register operations."""

    @staticmethod
    @transaction.atomic
    def recalculate_sale_totals(sale: POSSale) -> POSSale:
        items = sale.items.all()
        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        for item in items:
            line_total = item.quantity * item.unit_price - item.discount
            subtotal += line_total
            tax_amount += line_total * (item.tax_rate / Decimal("100"))
            item.line_total = _quantize_currency(line_total)
            item.save(update_fields=["line_total", "updated_at"])

        subtotal = _quantize_currency(subtotal)
        tax_amount = _quantize_currency(tax_amount)
        sale.subtotal = subtotal
        sale.tax_amount = tax_amount
        sale.total_amount = _quantize_currency(subtotal + tax_amount)
        sale.paid_amount = _quantize_currency(
            sum(payment.amount for payment in sale.payments.filter(status=POSSalePayment.Status.POSTED))
        )
        sale.change_due = _quantize_currency(sale.paid_amount - sale.total_amount)
        sale.save(
            update_fields=[
                "subtotal",
                "tax_amount",
                "total_amount",
                "paid_amount",
                "change_due",
                "updated_at",
            ]
        )
        return sale

    @staticmethod
    @transaction.atomic
    def finalize_sale(sale: POSSale, *, performed_by=None) -> POSSale:
        if sale.status == POSSale.Status.PAID:
            return sale

        items = list(sale.items.select_related("variant").all())
        if not items:
            raise ValueError("POS sale requires at least one item.")

        POSService.recalculate_sale_totals(sale)

        movement_lines = [
            StockMovementLineParams(
                variant=item.variant,
                warehouse=sale.warehouse,
                quantity=item.quantity * Decimal("-1"),
                unit_cost=None,
                metadata=item.metadata,
                reference_type="pos_sale",
                reference_id=str(sale.id),
                note=f"POS sale {sale.reference}",
            )
            for item in items
        ]

        movement = InventoryService.record_movement(
            tenant=sale.tenant,
            movement_type=StockMovement.MovementType.POS_SALE,
            lines=movement_lines,
            reference_number=sale.reference,
            description=f"POS sale {sale.reference}",
            performed_by=performed_by,
            source_document_type="pos_sale",
            source_document_id=str(sale.id),
            metadata=sale.metadata,
        )

        sale.stock_movement = movement
        sale.status = POSSale.Status.PAID
        sale.save(update_fields=["stock_movement", "status", "updated_at"])
        return sale

    @staticmethod
    @transaction.atomic
    def close_shift(shift: POSShift, *, closed_by=None, closing_float: Decimal | None = None) -> POSShift:
        if shift.status == POSShift.Status.CLOSED:
            return shift
        shift.status = POSShift.Status.CLOSED
        shift.closed_by = closed_by
        if closing_float is not None:
            shift.closing_float = closing_float
        shift.closed_at = shift.closed_at or shift.updated_at or shift.created_at
        shift.save(update_fields=["status", "closed_by", "closing_float", "closed_at", "updated_at"])
        return shift

    @staticmethod
    @transaction.atomic
    def mark_offline_item_synced(queue_item: POSOfflineQueueItem, *, error: str | None = None) -> POSOfflineQueueItem:
        if error:
            queue_item.status = POSOfflineQueueItem.Status.FAILED
            queue_item.error_message = error
        else:
            queue_item.status = POSOfflineQueueItem.Status.SYNCED
            queue_item.error_message = ""
        queue_item.save(update_fields=["status", "error_message", "updated_at"])
        return queue_item

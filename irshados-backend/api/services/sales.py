from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction

from ..models import (
    DeliveryNote,
    DeliveryNoteLine,
    SalesInvoice,
    SalesInvoiceLine,
    SalesOrder,
    SalesOrderLine,
    SalesPayment,
    SalesRefund,
    StockMovement,
)
from .inventory import InventoryService, StockMovementLineParams, DECIMAL_PRECISION_CURRENCY


def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_PRECISION_CURRENCY)


class SalesService:
    """Lifecycle helpers for the sales domain."""

    @staticmethod
    @transaction.atomic
    def post_delivery(delivery: DeliveryNote, *, performed_by=None) -> DeliveryNote:
        if delivery.status == DeliveryNote.Status.POSTED:
            return delivery

        lines = list(delivery.lines.select_related("order_line", "variant").all())
        if not lines:
            raise ValueError("Delivery note must contain at least one line before posting.")

        tenant = delivery.tenant
        order = delivery.order
        movement_lines: list[StockMovementLineParams] = []

        for line in lines:
            movement_lines.append(
                StockMovementLineParams(
                    variant=line.variant,
                    warehouse=delivery.warehouse,
                    quantity=line.quantity * Decimal("-1"),
                    metadata=line.metadata,
                    reference_type="sales_order",
                    reference_id=str(order.id),
                    note=f"Shipment {delivery.number}",
                )
            )

        movement = InventoryService.record_movement(
            tenant=tenant,
            movement_type=StockMovement.MovementType.SALE_SHIPMENT,
            lines=movement_lines,
            reference_number=delivery.number,
            description=f"Delivery for sales order {order.number}",
            performed_by=performed_by,
            source_document_type="delivery_note",
            source_document_id=str(delivery.id),
            metadata=delivery.notes and {"notes": delivery.notes} or {},
        )

        for line in lines:
            if line.order_line_id:
                order_line = line.order_line
                order_line.delivered_quantity = order_line.delivered_quantity + line.quantity
                order_line.save(update_fields=["delivered_quantity", "updated_at"])

        delivery.stock_movement = movement
        delivery.status = DeliveryNote.Status.POSTED
        delivery.save(update_fields=["status", "stock_movement", "updated_at"])

        SalesService._update_order_status(order)
        return delivery

    @staticmethod
    @transaction.atomic
    def post_invoice(invoice: SalesInvoice) -> SalesInvoice:
        if invoice.status == SalesInvoice.Status.POSTED:
            return invoice

        lines = list(invoice.lines.select_related("order_line").all())
        if not lines:
            raise ValueError("Sales invoice must contain at least one line before posting.")

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        for line in lines:
            line_total = line.quantity * line.unit_price
            subtotal += line_total
            tax_amount += line_total * (line.tax_rate / Decimal("100"))
            if line.order_line_id:
                order_line = line.order_line
                order_line.invoiced_quantity = order_line.invoiced_quantity + line.quantity
                order_line.save(update_fields=["invoiced_quantity", "updated_at"])

        subtotal = _quantize_currency(subtotal)
        tax_amount = _quantize_currency(tax_amount)
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = _quantize_currency(subtotal + tax_amount)
        invoice.status = SalesInvoice.Status.POSTED
        invoice.save(update_fields=["subtotal", "tax_amount", "total_amount", "status", "updated_at"])

        SalesService._update_order_status(invoice.order)
        return invoice

    @staticmethod
    @transaction.atomic
    def post_payment(payment: SalesPayment) -> SalesPayment:
        if payment.status == SalesPayment.Status.VOID:
            return payment
        invoice = payment.invoice
        total_paid = sum(
            (
                posted.amount
                for posted in invoice.payments.filter(status=SalesPayment.Status.POSTED).only("amount")
            ),
            start=Decimal("0"),
        )
        total_paid = _quantize_currency(total_paid)
        if total_paid >= invoice.total_amount:
            invoice.status = SalesInvoice.Status.PAID
            invoice.save(update_fields=["status", "updated_at"])
            SalesService._update_order_status(invoice.order)
        return payment

    @staticmethod
    def register_refund(refund: SalesRefund) -> SalesRefund:
        invoice = refund.invoice
        invoice.status = SalesInvoice.Status.PAID
        invoice.save(update_fields=["status", "updated_at"])
        SalesService._update_order_status(invoice.order)
        return refund

    @staticmethod
    def _update_order_status(order: SalesOrder) -> None:
        lines: Iterable[SalesOrderLine] = order.lines.only(
            "ordered_quantity", "delivered_quantity", "invoiced_quantity"
        )
        total_ordered = Decimal("0")
        total_delivered = Decimal("0")
        total_invoiced = Decimal("0")
        for line in lines:
            total_ordered += line.ordered_quantity
            total_delivered += line.delivered_quantity
            total_invoiced += line.invoiced_quantity

        previous_status = order.status
        if total_ordered == 0:
            order.status = SalesOrder.Status.DRAFT
        elif total_delivered >= total_ordered and total_invoiced >= total_ordered:
            order.status = SalesOrder.Status.PAID if order.invoices.filter(
                status=SalesInvoice.Status.PAID
            ).exists() else SalesOrder.Status.INVOICED
        elif total_delivered >= total_ordered:
            order.status = SalesOrder.Status.FULFILLED
        elif total_delivered > 0:
            order.status = SalesOrder.Status.PICKING
        else:
            order.status = SalesOrder.Status.CONFIRMED

        if order.status != previous_status:
            order.save(update_fields=["status", "updated_at"])

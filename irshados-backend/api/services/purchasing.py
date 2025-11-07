from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction

from ..models import (
    PurchaseBill,
    PurchaseBillLine,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchasePayment,
    PurchaseReceipt,
    PurchaseReceiptLine,
    StockMovement,
)
from .inventory import InventoryService, StockMovementLineParams, DECIMAL_PRECISION_CURRENCY


def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_PRECISION_CURRENCY)


class PurchasingService:
    """Domain utilities wrapping purchasing lifecycles."""

    @staticmethod
    @transaction.atomic
    def post_receipt(receipt: PurchaseReceipt, *, performed_by=None) -> PurchaseReceipt:
        if receipt.status == PurchaseReceipt.Status.POSTED:
            return receipt

        receipt_lines = list(
            receipt.lines.select_related("order_line", "variant").all()
        )  # evaluate once
        if not receipt_lines:
            raise ValueError("Purchase receipt must contain at least one line before posting.")

        order = receipt.order
        tenant = receipt.tenant
        lines: list[StockMovementLineParams] = []

        for line in receipt_lines:
            order_line: PurchaseOrderLine | None = line.order_line
            base_cost = order_line.unit_price if order_line else Decimal("0")
            unit_cost = line.unit_cost or base_cost
            lines.append(
                StockMovementLineParams(
                    variant=line.variant,
                    warehouse=receipt.warehouse,
                    quantity=line.quantity,
                    unit_cost=unit_cost,
                    metadata=line.metadata,
                    reference_type="purchase_order",
                    reference_id=str(order.id),
                    note=f"Receipt {receipt.number}",
                )
            )

        movement = InventoryService.record_movement(
            tenant=tenant,
            movement_type=StockMovement.MovementType.PURCHASE_RECEIPT,
            lines=lines,
            reference_number=receipt.number,
            description=f"Receipt for purchase order {order.number}",
            performed_by=performed_by,
            source_document_type="purchase_receipt",
            source_document_id=str(receipt.id),
            metadata=receipt.notes and {"notes": receipt.notes} or {},
        )

        for line in receipt_lines:
            if line.order_line_id:
                order_line = line.order_line
                order_line.received_quantity = order_line.received_quantity + line.quantity
                order_line.save(update_fields=["received_quantity", "updated_at"])

        receipt.stock_movement = movement
        receipt.status = PurchaseReceipt.Status.POSTED
        receipt.save(update_fields=["status", "stock_movement", "updated_at"])

        PurchasingService._update_order_status(order)
        return receipt

    @staticmethod
    @transaction.atomic
    def post_bill(bill: PurchaseBill) -> PurchaseBill:
        if bill.status == PurchaseBill.Status.POSTED:
            return bill

        lines = list(bill.lines.select_related("order_line").all())
        if not lines:
            raise ValueError("Purchase bill must contain at least one line before posting.")

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        for line in lines:
            line_total = line.quantity * line.unit_price
            subtotal += line_total
            tax_amount += line_total * (line.tax_rate / Decimal("100"))
            if line.order_line_id:
                order_line = line.order_line
                order_line.billed_quantity = order_line.billed_quantity + line.quantity
                order_line.save(update_fields=["billed_quantity", "updated_at"])

        subtotal = _quantize_currency(subtotal)
        tax_amount = _quantize_currency(tax_amount)
        bill.subtotal = subtotal
        bill.tax_amount = tax_amount
        bill.total_amount = _quantize_currency(subtotal + tax_amount)
        bill.status = PurchaseBill.Status.POSTED
        bill.save(update_fields=["subtotal", "tax_amount", "total_amount", "status", "updated_at"])

        PurchasingService._update_order_status(bill.order)
        return bill

    @staticmethod
    @transaction.atomic
    def post_payment(payment: PurchasePayment) -> PurchasePayment:
        if payment.status == PurchasePayment.Status.VOID:
            return payment

        bill = payment.bill
        total_paid = sum(
            (
                posted.amount
                for posted in bill.payments.filter(status=PurchasePayment.Status.POSTED).only("amount")
            ),
            start=Decimal("0"),
        )
        total_paid = _quantize_currency(total_paid)

        if total_paid >= bill.total_amount:
            bill.status = PurchaseBill.Status.PAID
            bill.save(update_fields=["status", "updated_at"])
            PurchasingService._update_order_status(bill.order)
        return payment

    @staticmethod
    def _update_order_status(order: PurchaseOrder) -> None:
        lines: Iterable[PurchaseOrderLine] = order.lines.only(
            "ordered_quantity", "received_quantity", "billed_quantity"
        )
        total_ordered = Decimal("0")
        total_received = Decimal("0")
        total_billed = Decimal("0")
        for line in lines:
            total_ordered += line.ordered_quantity
            total_received += line.received_quantity
            total_billed += line.billed_quantity

        previous_status = order.status
        if total_ordered == 0:
            order.status = PurchaseOrder.Status.DRAFT
        elif total_received >= total_ordered and total_billed >= total_ordered:
            order.status = PurchaseOrder.Status.PAID if order.bills.filter(
                status=PurchaseBill.Status.PAID
            ).exists() else PurchaseOrder.Status.BILLED
        elif total_received >= total_ordered:
            order.status = PurchaseOrder.Status.RECEIVED
        elif total_received > 0:
            order.status = PurchaseOrder.Status.RECEIVING
        else:
            order.status = PurchaseOrder.Status.SUBMITTED

        if order.status != previous_status:
            order.save(update_fields=["status", "updated_at"])

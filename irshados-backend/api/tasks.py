from __future__ import annotations

from decimal import Decimal

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import (
    AuditLog,
    Invitation,
    KitchenOrderTicket,
    MenuItem,
    RecipeComponent,
    Tenant,
)

logger = logging.getLogger("irshados.audit")


@shared_task(name="api.send_invitation_email")
def send_invitation_email(invitation_id: str) -> None:
    try:
        invitation = Invitation.objects.select_related("tenant").get(id=invitation_id)
    except Invitation.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("Invitation %s not found for email dispatch", invitation_id)
        return

    subject = f"You're invited to join {invitation.tenant.name} on IrshadOS"
    message = (
        f"Hello,\n\nYou have been invited to join {invitation.tenant.name} on IrshadOS as "
        f"a {invitation.role.name}. Use the token below to accept your invite before "
        f"{invitation.expires_at.strftime('%Y-%m-%d %H:%M %Z')}.\n\n"
        f"Invitation Token: {invitation.token}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@irshados.dev"),
        recipient_list=[invitation.email],
        fail_silently=True,
    )
    logger.info("Invitation email queued for %s", invitation.email)


@shared_task(name="api.export_audit_log")
def export_audit_log(tenant_id: str) -> int:
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("Tenant %s not found for audit export", tenant_id)
        return 0

    cutoff = timezone.now() - timedelta(days=30)
    records = AuditLog.objects.filter(tenant=tenant, created_at__gte=cutoff).count()
    logger.info("Prepared audit log export for %s (%s records)", tenant.slug, records)
    return records


@shared_task(name="api.restaurant.dispatch_kitchen_ticket")
def dispatch_kitchen_ticket(ticket_id: str) -> None:
    try:
        ticket = KitchenOrderTicket.objects.get(id=ticket_id)
    except KitchenOrderTicket.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("Kitchen ticket %s not found for dispatch", ticket_id)
        return
    logger.info(
        "Dispatching kitchen ticket %s (%s items) for tenant %s",
        ticket.ticket_number,
        ticket.lines.count(),
        ticket.tenant.slug,
    )


@shared_task(name="api.restaurant.compile_recipe_cost_report")
def compile_recipe_cost_report(tenant_id: str) -> dict:
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("Tenant %s not found for recipe cost report", tenant_id)
        return {}

    summary: dict[str, float] = {}
    recipes = (
        RecipeComponent.objects.filter(tenant=tenant)
        .select_related("recipe__item", "ingredient")
        .order_by("recipe__item__name")
    )
    for component in recipes:
        item_name = component.recipe.item.name
        base_cost = float(component.ingredient.cost_price or Decimal("0"))
        summary.setdefault(item_name, 0.0)
        summary[item_name] += base_cost * float(component.quantity)

    logger.info(
        "Compiled recipe cost report for %s (%s entries)",
        tenant.slug,
        len(summary),
    )
    return summary



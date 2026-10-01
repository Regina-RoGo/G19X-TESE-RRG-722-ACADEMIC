from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from sqlmodel import Session

from app.models.customer_insight import ChurnRisk
from app.models.deal import DealStage
from app.repositories import (
    customer_repository,
    deal_repository,
    interaction_repository,
    task_repository,
)
from app.services.deal_service import CLOSED_STAGE_PROBABILITY, STAGE_LABELS

# Un cliente es "activo" si tuvo contacto en esta ventana o tiene un deal abierto.
ACTIVE_CUSTOMER_WINDOW_DAYS = 30
# Días que cubre el gráfico de actividad de interacciones.
ACTIVITY_CHART_DAYS = 30
RECENT_ACTIVITY_LIMIT = 8

CHURN_LABELS = {ChurnRisk.BAJO: "Bajo", ChurnRisk.MEDIO: "Medio", ChurnRisk.ALTO: "Alto"}


def _pipeline_stages(session: Session) -> List[dict]:
    summary = deal_repository.stage_summary(session)
    empty = {"count": 0, "total": Decimal("0"), "weighted": Decimal("0")}
    return [
        {"stage": stage, "label": label, **summary.get(stage, empty)}
        for stage, label in STAGE_LABELS.items()
    ]


def _kpis(session: Session, stages: List[dict]) -> dict:
    by_stage = {row["stage"]: row for row in stages}
    open_stages = [row for row in stages if row["stage"] not in CLOSED_STAGE_PROBABILITY]
    won = by_stage[DealStage.CLOSED_WON]
    lost = by_stage[DealStage.CLOSED_LOST]
    closed_count = won["count"] + lost["count"]
    today = date.today()

    return {
        "revenue": won["total"],
        "won_count": won["count"],
        "pipeline_value": sum((row["total"] for row in open_stages), Decimal("0")),
        "pipeline_weighted": sum((row["weighted"] for row in open_stages), Decimal("0")),
        "open_deals": sum(row["count"] for row in open_stages),
        "active_customers": customer_repository.count_active(
            session, datetime.utcnow() - timedelta(days=ACTIVE_CUSTOMER_WINDOW_DAYS)
        ),
        "total_customers": customer_repository.count(session),
        # Tasa de cierre: ganados sobre deals cerrados (ganados + perdidos).
        "conversion_rate": round(won["count"] * 100 / closed_count) if closed_count else None,
        "closed_count": closed_count,
        "pending_tasks": task_repository.count_pending(session),
        "overdue_tasks": task_repository.count_pending(session, overdue_before=today),
    }


def _recent_activity(session: Session) -> List[dict]:
    """Interacciones y deals recientes mezclados en una sola línea de tiempo."""
    events = [
        {
            "kind": "interaction",
            "at": interaction.occurred_at,
            "customer_id": interaction.customer_id,
            "customer_name": interaction.customer.name,
            "label": interaction.interaction_type.name,
            "text": interaction.notes,
        }
        for interaction in interaction_repository.get_recent(session, RECENT_ACTIVITY_LIMIT)
    ]
    for deal in deal_repository.get_recent(session, RECENT_ACTIVITY_LIMIT):
        # Un deal sin cambios posteriores a su alta se muestra como "nuevo".
        is_new = (deal.updated_at - deal.created_at) < timedelta(seconds=1)
        events.append(
            {
                "kind": "deal",
                "at": deal.updated_at,
                "customer_id": deal.customer_id,
                "customer_name": deal.customer.name,
                "label": "Nuevo deal" if is_new else "Deal actualizado",
                "text": deal.title,
                "stage": deal.stage,
                "value": deal.value,
            }
        )
    events.sort(key=lambda event: event["at"], reverse=True)
    return events[:RECENT_ACTIVITY_LIMIT]


def _charts(session: Session, stages: List[dict]) -> dict:
    start = date.today() - timedelta(days=ACTIVITY_CHART_DAYS - 1)
    per_day = interaction_repository.count_by_day(
        session, datetime.combine(start, datetime.min.time())
    )
    days = [start + timedelta(days=offset) for offset in range(ACTIVITY_CHART_DAYS)]
    churn = customer_repository.churn_distribution(session)

    # Solo tipos JSON simples: el template los serializa con |tojson para Chart.js.
    return {
        "pipeline": {
            "labels": [row["label"] for row in stages],
            "values": [float(row["total"]) for row in stages],
            "counts": [row["count"] for row in stages],
        },
        "activity": {
            "labels": [day.strftime("%d/%m") for day in days],
            "values": [per_day.get(day, 0) for day in days],
        },
        "churn": {
            "labels": list(CHURN_LABELS.values()),
            "values": [churn.get(level, 0) for level in CHURN_LABELS],
        },
    }


def get_dashboard_data(session: Session) -> dict:
    stages = _pipeline_stages(session)
    return {
        "kpis": _kpis(session, stages),
        "pipeline_stages": stages,
        "pipeline_max": max((row["total"] for row in stages), default=Decimal("0")),
        "recent_activity": _recent_activity(session),
        "charts": _charts(session, stages),
    }

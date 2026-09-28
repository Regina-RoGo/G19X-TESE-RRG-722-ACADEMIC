from datetime import date, datetime, timedelta
from typing import List, Type, TypeVar

import httpx
from fastapi import HTTPException, status
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.models.ai_summary import AISummary, Sentiment
from app.models.customer import Customer
from app.models.customer_insight import ChurnRisk, CustomerInsight
from app.models.deal import Deal, DealStage
from app.models.interaction import Interaction
from app.models.sales_suggestion import SalesSuggestion
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories import (
    ai_summary_repository,
    customer_insight_repository,
    deal_repository,
    interaction_repository,
    sales_suggestion_repository,
    task_repository,
)
from app.services import customer_tag_service

MODEL_NAME = "gemini-3.6-flash"
MAX_ATTEMPTS = 2  # intento inicial + 1 reintento automático (timeout: GEMINI_TIMEOUT_SECONDS)

SUMMARY_SYSTEM_INSTRUCTION = (
    "Eres un asistente comercial que redacta resúmenes ejecutivos para un equipo de ventas. "
    "A partir del historial de interacciones con un cliente, produce un resumen breve, claro "
    "y accionable, basado únicamente en la información provista, y clasificas el sentimiento "
    "general del cliente."
)

SALES_SUGGESTIONS_SYSTEM_INSTRUCTION = (
    "Eres un asesor comercial senior que ayuda a un vendedor a avanzar y cerrar oportunidades. "
    "A partir del historial de interacciones y de los deals del cliente, propones próximos pasos "
    "concretos y una estrategia de cierre realista, basada únicamente en la información provista."
)

INSIGHTS_SYSTEM_INSTRUCTION = (
    "Eres un analista comercial que evalúa clientes de un CRM. A partir del perfil del cliente, "
    "su historial de interacciones y sus deals, estimas su potencial de compra (lead scoring), "
    "su riesgo de abandono (churn), sugieres etiquetas de segmentación y tareas de seguimiento. "
    "Te basas únicamente en la información provista y justificas cada evaluación con hechos concretos."
)

MAX_SUGGESTED_TAGS = 5
MAX_SUGGESTED_TASKS = 3
MAX_TASK_DUE_DAYS = 90

# Etapas legibles para el prompt (mismo vocabulario que ve el usuario en el Pipeline).
STAGE_NAMES = {
    DealStage.PROSPECT: "Prospecto",
    DealStage.CONTACTED: "Contactado",
    DealStage.PROPOSAL_SENT: "Propuesta Enviada",
    DealStage.CLOSED_WON: "Ganado",
    DealStage.CLOSED_LOST: "Perdido",
}
CLOSED_STAGES = (DealStage.CLOSED_WON, DealStage.CLOSED_LOST)

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class AIServiceError(Exception):
    """Error controlado al usar Gemini (servicio caído, timeout, sin API key, respuesta inválida, etc.)."""


class _GeminiSummaryResponse(BaseModel):
    resumen: str
    sentimiento: Sentiment


class _GeminiSalesSuggestionResponse(BaseModel):
    proximos_pasos: List[str]
    estrategia_cierre: str


class _GeminiSuggestedTask(BaseModel):
    titulo: str
    prioridad: TaskPriority
    dias_para_vencer: int


class _GeminiInsightsResponse(BaseModel):
    lead_score: int
    justificacion_lead_score: str
    riesgo_churn: ChurnRisk
    justificacion_churn: str
    tags: List[str]
    tareas_sugeridas: List[_GeminiSuggestedTask]


def _interaction_lines(interactions: List[Interaction]) -> List[str]:
    lines = ["Historial de interacciones (de la más reciente a la más antigua):"]
    for interaction in interactions:
        type_name = interaction.interaction_type.name if interaction.interaction_type else "N/D"
        author = interaction.user.full_name if interaction.user else "N/D"
        fecha = interaction.occurred_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"- [{fecha}] ({type_name}, registrado por {author}): {interaction.notes}")
    return lines


def _deal_line(deal: Deal) -> str:
    return (
        f"- {deal.title} | etapa: {STAGE_NAMES[deal.stage]} | monto: {deal.value:,.2f} | "
        f"probabilidad: {deal.probability} % | última actualización: {deal.updated_at:%Y-%m-%d}"
    )


def _build_prompt(customer: Customer, interactions: List[Interaction]) -> str:
    lines = [f"Cliente: {customer.name}", "", *_interaction_lines(interactions)]

    lines.extend(
        [
            "",
            "Redacta un resumen ejecutivo comercial en español con exactamente estas tres "
            "secciones (usa esos títulos) para el campo 'resumen':",
            "1. Puntos clave",
            "2. Estado/sentimiento del cliente",
            "3. Siguientes pasos recomendados",
            "",
            "Además, en el campo 'sentimiento' clasifica el tono general del cliente en "
            "exactamente uno de estos tres valores:",
            "- POSITIVO: satisfecho, conforme o con intención de avanzar/comprar.",
            "- NEUTRAL: interacción informativa o de rutina, sin señales claras en ningún sentido.",
            "- NEGATIVO: quejas, frustración o señales de insatisfacción.",
        ]
    )
    return "\n".join(lines)


def _build_sales_prompt(
    customer: Customer, interactions: List[Interaction], deals: List[Deal]
) -> str:
    active_deals = [deal for deal in deals if deal.stage not in CLOSED_STAGES]
    closed_deals = [deal for deal in deals if deal.stage in CLOSED_STAGES]

    lines = [f"Cliente: {customer.name}", "", *_interaction_lines(interactions), ""]
    lines.append("Deals activos (oportunidades abiertas):")
    lines.extend([_deal_line(deal) for deal in active_deals] or ["- Ninguno."])
    if closed_deals:
        lines.extend(["", "Deals cerrados (contexto histórico):"])
        lines.extend(_deal_line(deal) for deal in closed_deals)

    lines.extend(
        [
            "",
            "Responde en español:",
            "- 'proximos_pasos': entre 3 y 5 acciones concretas, ordenadas por prioridad, que el "
            "vendedor debería ejecutar ahora (cada una en una oración, mencionando el deal si aplica).",
            "- 'estrategia_cierre': un párrafo breve con la estrategia recomendada para cerrar los "
            "deals activos (o, si no hay ninguno, para abrir una nueva oportunidad con este cliente), "
            "incluyendo riesgos u objeciones a anticipar.",
        ]
    )
    return "\n".join(lines)


def _build_insights_prompt(
    customer: Customer,
    interactions: List[Interaction],
    deals: List[Deal],
    pending_tasks: List[Task],
) -> str:
    today = date.today()
    lines = [
        f"Fecha de hoy: {today:%Y-%m-%d}",
        "",
        "Perfil del cliente:",
        f"- Nombre: {customer.name}",
        f"- Empresa: {customer.company or 'N/D'}",
        f"- Email: {'sí' if customer.email else 'no'} | Teléfono: {'sí' if customer.phone else 'no'}",
        f"- Cliente desde: {customer.created_at:%Y-%m-%d}",
        "",
        *_interaction_lines(interactions),
        "",
        "Deals (oportunidades):",
    ]
    lines.extend([_deal_line(deal) for deal in deals] or ["- Ninguno."])
    lines.extend(["", "Tareas de seguimiento ya pendientes (no las repitas):"])
    lines.extend(
        [
            f"- {task.title} (vence: {task.due_date or 'sin fecha'})"
            for task in pending_tasks
        ]
        or ["- Ninguna."]
    )

    lines.extend(
        [
            "",
            "Responde en español:",
            "- 'lead_score': entero de 0 a 100 con la probabilidad/potencial de que este cliente "
            "genere negocio (considera interés mostrado, deals abiertos, montos y avance de etapa).",
            "- 'justificacion_lead_score': 1–3 oraciones citando los hechos que explican el puntaje.",
            "- 'riesgo_churn': exactamente uno de BAJO, MEDIO o ALTO (riesgo de que el cliente deje "
            "de comprar o abandone la relación: quejas, silencio prolongado, deals perdidos, etc.).",
            "- 'justificacion_churn': 1–3 oraciones citando los hechos que explican el nivel.",
            f"- 'tags': entre 1 y {MAX_SUGGESTED_TAGS} etiquetas cortas de segmentación (1–3 palabras, "
            "en minúsculas, ej. 'alto valor', 'sensible a precio', 'renovación próxima').",
            f"- 'tareas_sugeridas': entre 1 y {MAX_SUGGESTED_TASKS} tareas de seguimiento concretas "
            "para el vendedor, cada una con 'titulo' (una oración imperativa), 'prioridad' "
            f"(LOW, MEDIUM o HIGH) y 'dias_para_vencer' (entero de 0 a {MAX_TASK_DUE_DAYS}, "
            "contado desde hoy).",
        ]
    )
    return "\n".join(lines)


def _call_gemini(
    prompt: str,
    system_instruction: str,
    response_schema: Type[ResponseModel],
    task_description: str,
) -> ResponseModel:
    """Llamada única a Gemini con salida estructurada, timeout configurable y 1 reintento."""
    if not settings.gemini_api_key:
        raise AIServiceError("GEMINI_API_KEY no está configurada.")

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=genai_types.HttpOptions(timeout=settings.gemini_timeout_seconds * 1000),
    )

    last_error: Exception = AIServiceError("Fallo desconocido al llamar a Gemini.")
    for _ in range(MAX_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
            parsed = response.parsed
            if not isinstance(parsed, response_schema):
                raise AIServiceError("Gemini devolvió una respuesta vacía o inválida.")
            return parsed
        except (httpx.TimeoutException, httpx.ConnectError, genai_errors.APIError) as exc:
            last_error = exc

    raise AIServiceError(
        f"No se pudo {task_description} tras {MAX_ATTEMPTS} intento(s): {last_error}"
    ) from last_error


def generate_summary(session: Session, customer: Customer) -> AISummary:
    interactions = interaction_repository.get_by_customer(session, customer.id)
    if not interactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente no tiene interacciones registradas; no es posible generar un resumen.",
        )

    prompt = _build_prompt(customer, interactions)
    result = _call_gemini(
        prompt, SUMMARY_SYSTEM_INSTRUCTION, _GeminiSummaryResponse, "generar el resumen ejecutivo"
    )
    if not result.resumen.strip():
        raise AIServiceError("Gemini devolvió una respuesta vacía o inválida.")

    ai_summary = AISummary(
        customer_id=customer.id,
        content=result.resumen,
        sentiment=result.sentimiento.value,
    )
    return ai_summary_repository.create(session, ai_summary)


def generate_sales_suggestions(session: Session, customer: Customer) -> SalesSuggestion:
    interactions = interaction_repository.get_by_customer(session, customer.id)
    if not interactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El cliente no tiene interacciones registradas; registre al menos una "
                "para poder generar sugerencias de venta."
            ),
        )
    deals = deal_repository.get_by_customer(session, customer.id)

    prompt = _build_sales_prompt(customer, interactions, deals)
    result = _call_gemini(
        prompt,
        SALES_SUGGESTIONS_SYSTEM_INSTRUCTION,
        _GeminiSalesSuggestionResponse,
        "generar las sugerencias de venta",
    )

    next_steps = [step.strip() for step in result.proximos_pasos if step.strip()]
    if not next_steps or not result.estrategia_cierre.strip():
        raise AIServiceError("Gemini devolvió una respuesta vacía o inválida.")

    suggestion = SalesSuggestion(
        customer_id=customer.id,
        next_steps=next_steps,
        closing_strategy=result.estrategia_cierre.strip(),
    )
    return sales_suggestion_repository.create(session, suggestion)


def _normalize_tags(tags: List[str]) -> List[str]:
    normalized: List[str] = []
    for tag in tags:
        clean = customer_tag_service.normalize_tag_name(tag)
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized[:MAX_SUGGESTED_TAGS]


def get_latest_insights(session: Session, customer: Customer) -> CustomerInsight:
    insight = customer_insight_repository.get_latest_by_customer(session, customer.id)
    if insight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente aún no tiene un análisis predictivo generado.",
        )
    return insight


def generate_insights(session: Session, customer: Customer) -> CustomerInsight:
    interactions = interaction_repository.get_by_customer(session, customer.id)
    if not interactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El cliente no tiene interacciones registradas; registre al menos una "
                "para poder generar el análisis predictivo."
            ),
        )
    deals = deal_repository.get_by_customer(session, customer.id)
    pending_tasks = task_repository.get_all(
        session, customer_id=customer.id, status=TaskStatus.PENDING
    )

    prompt = _build_insights_prompt(customer, interactions, deals, pending_tasks)
    result = _call_gemini(
        prompt,
        INSIGHTS_SYSTEM_INSTRUCTION,
        _GeminiInsightsResponse,
        "generar el análisis predictivo",
    )

    lead_justification = result.justificacion_lead_score.strip()
    churn_justification = result.justificacion_churn.strip()
    if not lead_justification or not churn_justification:
        raise AIServiceError("Gemini devolvió una respuesta vacía o inválida.")

    # response_schema no garantiza rangos numéricos: se acotan aquí.
    generated_at = datetime.utcnow()
    suggested_tasks = [
        {
            "title": task.titulo.strip(),
            "priority": task.prioridad.value,
            "due_date": (
                generated_at.date()
                + timedelta(days=min(max(task.dias_para_vencer, 0), MAX_TASK_DUE_DAYS))
            ).isoformat(),
        }
        for task in result.tareas_sugeridas
        if task.titulo.strip()
    ][:MAX_SUGGESTED_TASKS]

    insight = CustomerInsight(
        customer_id=customer.id,
        lead_score=min(max(result.lead_score, 0), 100),
        lead_score_justification=lead_justification,
        churn_risk=result.riesgo_churn,
        churn_justification=churn_justification,
        suggested_tags=_normalize_tags(result.tags),
        suggested_tasks=suggested_tasks,
        generated_at=generated_at,
    )
    return customer_insight_repository.create(session, insight)

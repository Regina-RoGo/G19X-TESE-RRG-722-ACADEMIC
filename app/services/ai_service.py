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
from app.models.deal import Deal, DealStage
from app.models.interaction import Interaction
from app.models.sales_suggestion import SalesSuggestion
from app.repositories import (
    ai_summary_repository,
    deal_repository,
    interaction_repository,
    sales_suggestion_repository,
)

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

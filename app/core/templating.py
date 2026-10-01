import json
from datetime import date

from fastapi import Request, Response
from fastapi.templating import Jinja2Templates

from app.services import deal_service, task_service

# Instancia única de Jinja2 compartida por los routers de páginas.
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["money"] = lambda value: f"$ {value:,.2f}"
templates.env.globals["stage_labels"] = deal_service.STAGE_LABELS
templates.env.globals["priority_labels"] = {
    priority.value: label for priority, label in task_service.PRIORITY_LABELS.items()
}
templates.env.globals["today"] = date.today


def toast(response: Response, message: str, level: str = "success") -> Response:
    """Pide al frontend un toast vía el evento HTMX `showToast` (ver partials/_toast.html)."""
    # ensure_ascii: los headers HTTP van en latin-1; los acentos viajan como \\uXXXX.
    response.headers["HX-Trigger"] = json.dumps(
        {"showToast": {"message": message, "level": level}}, ensure_ascii=True
    )
    return response


def ai_error(exc: Exception) -> tuple:
    """Mensaje y nivel de toast para un fallo de un fragmento de IA.

    Un HTTPException es de validación (ej. cliente sin interacciones) → advertencia;
    un AIServiceError es una falla de Gemini tras el reintento → error.
    """
    detail = getattr(exc, "detail", None)
    if isinstance(detail, str):
        return detail, "warning"
    return str(exc), "error"


def form_error(request: Request, message: str, target: str):
    # El formulario apunta a una lista/tablero; ante un error se redirige el swap
    # a la alerta del propio formulario en vez de reemplazar el contenido.
    response = templates.TemplateResponse(
        request, "partials/form_error.html", {"error": message}
    )
    response.headers["HX-Retarget"] = target
    response.headers["HX-Reswap"] = "innerHTML"
    return toast(response, message, "warning")

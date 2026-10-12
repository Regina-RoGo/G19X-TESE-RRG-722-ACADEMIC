from typing import Dict

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """Formato de todos los errores controlados de la API (HTTPException de FastAPI)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"detail": "Cliente no encontrado"}]})

    detail: str


class MessageResponse(BaseModel):
    message: str


_ERROR_DESCRIPTIONS = {
    400: "Solicitud no procesable por el estado de los datos (ej. cliente sin interacciones).",
    401: "No autenticado: falta la cookie de sesión o el token es inválido/expiró.",
    403: "El rol del usuario no tiene permiso para esta acción (requiere `admin`).",
    404: "El recurso indicado no existe.",
    409: "Conflicto con el estado actual (ej. duplicado o registros asociados).",
    502: "Gemini no respondió correctamente tras el reintento automático.",
}


def error_responses(*codes: int) -> Dict[int, dict]:
    """Bloque `responses` de OpenAPI para los códigos de error de un endpoint."""
    return {
        code: {"model": ErrorResponse, "description": _ERROR_DESCRIPTIONS[code]} for code in codes
    }

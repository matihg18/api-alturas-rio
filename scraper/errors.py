"""Utilidades de clasificación de errores de scraping."""
import requests


def classify_error(e: Exception) -> tuple[str, int | None]:
    """Clasifica una excepción de scraping en un tipo canónico.

    Devuelve (error_type, http_status_code).
    - HTTP_ERROR  : la respuesta HTTP trajo un código de error (4xx/5xx)
    - TIMEOUT     : la conexión/lectura superó el tiempo límite
    - PARSE_ERROR : la respuesta llegó pero no se pudo parsear
    - UNKNOWN     : cualquier otra excepción inesperada
    """
    if isinstance(e, requests.exceptions.Timeout):
        return "TIMEOUT", None

    if isinstance(e, requests.exceptions.HTTPError):
        status = None
        if e.response is not None:
            status = e.response.status_code
        return "HTTP_ERROR", status

    if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.RequestException)):
        return "HTTP_ERROR", None

    # Errores de parseo comunes (JSON, BeautifulSoup, regex, etc.)
    if isinstance(e, (ValueError, KeyError, AttributeError, TypeError, IndexError)):
        return "PARSE_ERROR", None

    return "UNKNOWN", None

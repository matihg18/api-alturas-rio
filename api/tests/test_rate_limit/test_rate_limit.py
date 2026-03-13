import os
import pytest

# Configurar un rate limit bajo ANTES de importar la app
os.environ["RATE_LIMIT_DEFAULT"] = "3/minute"

from fastapi.testclient import TestClient  # noqa: E402
from api.rate_limiter import limiter  # noqa: E402
from api.main import app, get_db  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402


@pytest.fixture(autouse=True)
def reset_limiter():
    """Limpiar el estado del limiter entre cada test."""
    limiter.reset()
    yield


@pytest.fixture()
def client():
    """Cliente de test con dependencia de DB mockeada."""
    mock_session = MagicMock()

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_requests_within_limit_succeed(client):
    """Las solicitudes dentro del límite deben ser procesadas (no 429)."""
    for i in range(3):
        response = client.get("/ports")
        assert response.status_code != 429, f"Request {i+1} fue rechazada por rate limit"


def test_requests_exceeding_limit_return_429(client):
    """Al exceder el límite, se debe recibir un 429."""
    # Agotar el límite (3 solicitudes)
    for _ in range(3):
        client.get("/ports")

    # La 4ta solicitud debería ser rechazada
    response = client.get("/ports")
    assert response.status_code == 429


def test_rate_limit_response_has_error_detail(client):
    """La respuesta 429 debe incluir un mensaje descriptivo."""
    for _ in range(3):
        client.get("/ports")

    response = client.get("/ports")
    assert response.status_code == 429
    data = response.json()
    assert "error" in data or "detail" in data



def test_rate_limit_applies_per_endpoint(client):
    """El rate limit aplica de forma independiente por endpoint."""
    # Agotar el límite en /ports
    for _ in range(3):
        client.get("/ports")

    # Verificar que /ports fue limitado
    response = client.get("/ports")
    assert response.status_code == 429

    # /alerts debería seguir disponible (tiene su propio contador)
    response = client.get("/alerts")
    assert response.status_code != 429

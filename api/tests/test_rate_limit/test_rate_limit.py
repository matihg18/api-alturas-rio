import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from unittest.mock import MagicMock

TEST_RATE_LIMIT = "3/minute"


def create_test_app():
    """Crea una instancia fresca de FastAPI con rate limit de test."""
    test_limiter = Limiter(key_func=get_remote_address)

    test_app = FastAPI()
    test_app.state.limiter = test_limiter
    test_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    test_app.add_middleware(SlowAPIMiddleware)

    mock_session = MagicMock()

    def get_db():
        yield mock_session

    @test_app.get("/ports")
    @test_limiter.limit(TEST_RATE_LIMIT)
    def get_ports(request: Request):
        return {"data": [], "page": 1, "page_size": 10, "total": 0}

    @test_app.get("/alerts")
    @test_limiter.limit(TEST_RATE_LIMIT)
    def get_alerts(request: Request):
        return {"data": [], "page": 1, "page_size": 10, "total": 0}

    return test_app, test_limiter


@pytest.fixture(autouse=True)
def rate_limit_app():
    """Crea una app fresca con rate limit configurado para cada test."""
    test_app, test_limiter = create_test_app()
    test_limiter.reset()
    return test_app, test_limiter


@pytest.fixture()
def client(rate_limit_app):
    """Cliente de test con rate limit bajo."""
    test_app, _ = rate_limit_app
    with TestClient(test_app) as c:
        yield c


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

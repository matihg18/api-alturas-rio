"""Tests para el manejo de errores en las estrategias de scraping.

Verifica que cuando un cliente HTTP lanza una excepción, la estrategia:
  1. Llama a on_error con los argumentos correctos.
  2. Continúa con las demás estaciones (no aborta el loop).
  3. Devuelve resultados parciales (las estaciones que sí funcionaron).
"""
import pytest
import requests
from unittest.mock import MagicMock, call


# ─── Prefectura Incremental ────────────────────────────────────────────────────

def test_prefectura_incremental_calls_on_error_on_http_failure(monkeypatch):
    """Si fetch_data lanza HTTPError, on_error debe ser llamado con HTTP_ERROR."""
    from scraper.prefectura.strategy import PrefecturaIncrementalStrategy

    monkeypatch.setenv("BASE_SOURCE_URL", "http://example.com/")
    strategy = PrefecturaIncrementalStrategy()

    strategy.client.fetch_data = MagicMock(
        side_effect=requests.exceptions.HTTPError(response=_make_response(500))
    )
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    assert stations == []
    assert measurements == []
    on_error.assert_called_once()
    kwargs = on_error.call_args.kwargs
    assert kwargs["source"] == "Prefectura"
    assert kwargs["error_type"] == "HTTP_ERROR"
    assert kwargs["http_status_code"] == 500
    assert kwargs["station_name"] is None


def test_prefectura_incremental_no_on_error_does_not_raise(monkeypatch):
    """Si no se pasa on_error y hay un error, no debe lanzar."""
    from scraper.prefectura.strategy import PrefecturaIncrementalStrategy

    monkeypatch.setenv("BASE_SOURCE_URL", "http://example.com/")
    strategy = PrefecturaIncrementalStrategy()
    strategy.client.fetch_data = MagicMock(side_effect=requests.exceptions.Timeout())

    stations, measurements = strategy.get_data(on_error=None)

    assert stations == []
    assert measurements == []


# ─── Prefectura BackFill ───────────────────────────────────────────────────────

def test_prefectura_backfill_calls_on_error_per_station(monkeypatch, html_pagina_principal):
    """Si una estación falla en backfill, on_error se llama por esa estación
    y el loop continúa con las demás (aquí ambas fallan, se esperan 2 calls)."""
    from scraper.prefectura.strategy import PrefecturaBackFillStrategy

    monkeypatch.setenv("BASE_SOURCE_URL", "http://example.com/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")
    strategy = PrefecturaBackFillStrategy(backfill_days=7)

    # Primera llamada devuelve el HTML principal; el resto lanza timeout
    strategy.client.fetch_data = MagicMock(
        side_effect=[html_pagina_principal, requests.exceptions.Timeout(), requests.exceptions.Timeout()]
    )
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    # html_pagina_principal tiene 2 estaciones → 2 errores de timeout
    assert on_error.call_count == 2
    for c in on_error.call_args_list:
        assert c.kwargs["error_type"] == "TIMEOUT"
        assert c.kwargs["source"] == "Prefectura"
        assert c.kwargs["station_name"] is not None  # debe saber qué estación

    assert measurements == []


def test_prefectura_backfill_main_page_failure_calls_on_error(monkeypatch):
    """Si falla la request de la página principal, on_error se llama sin station_name."""
    from scraper.prefectura.strategy import PrefecturaBackFillStrategy

    monkeypatch.setenv("BASE_SOURCE_URL", "http://example.com/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")
    strategy = PrefecturaBackFillStrategy(backfill_days=7)
    strategy.client.fetch_data = MagicMock(side_effect=requests.exceptions.ConnectionError())
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    on_error.assert_called_once()
    assert on_error.call_args.kwargs["station_name"] is None
    assert on_error.call_args.kwargs["source"] == "Prefectura"


def test_prefectura_backfill_partial_failure_continues(monkeypatch, html_pagina_principal, html_historico_normal):
    """Si solo una estación falla, la otra sigue siendo scrapeada."""
    from scraper.prefectura.strategy import PrefecturaBackFillStrategy

    monkeypatch.setenv("BASE_SOURCE_URL", "http://example.com/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")
    strategy = PrefecturaBackFillStrategy(backfill_days=7)

    # html_pagina_principal tiene 2 estaciones: primera falla, segunda ok
    strategy.client.fetch_data = MagicMock(
        side_effect=[html_pagina_principal, requests.exceptions.Timeout(), html_historico_normal]
    )
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    assert on_error.call_count == 1  # solo una falla
    assert len(measurements) > 0    # la segunda sí trajo datos


# ─── INA ──────────────────────────────────────────────────────────────────────

def test_ina_incremental_calls_on_error_on_observations_failure(monkeypatch):
    """Si get_observations falla para una serie, on_error se llama con station_name."""
    from scraper.ina.strategy import INAIncrementalStrategy

    monkeypatch.setenv("INA_API_BASE_URL", "https://alerta.ina.gob.ar/a5")
    monkeypatch.setenv("ALLOWED_RIVERS", "")
    strategy = INAIncrementalStrategy()

    series_list = [
        {"id": 42, "estacion": {"nombre": "COLON", "rio": "URUGUAY"}},
        {"id": 43, "estacion": {"nombre": "CONCORDIA", "rio": "URUGUAY"}},
    ]
    strategy.client.get_series = MagicMock(return_value=series_list)
    # COLON falla, CONCORDIA ok
    strategy.client.get_observations = MagicMock(
        side_effect=[
            requests.exceptions.HTTPError(response=_make_response(404)),
            [{"timestart": "2026-01-01T12:00:00Z", "valor": 2.15}],
        ]
    )
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    on_error.assert_called_once()
    kwargs = on_error.call_args.kwargs
    assert kwargs["source"] == "INA"
    assert kwargs["error_type"] == "HTTP_ERROR"
    assert kwargs["station_name"] == "COLON"
    assert kwargs["http_status_code"] == 404

    # CONCORDIA sí debe tener medición
    assert len(measurements) == 1
    assert measurements[0].station_name == "CONCORDIA"


def test_ina_incremental_series_failure_calls_on_error_without_station(monkeypatch):
    """Si get_series falla (request de descubrimiento), on_error se llama sin station_name."""
    from scraper.ina.strategy import INAIncrementalStrategy

    monkeypatch.setenv("INA_API_BASE_URL", "https://alerta.ina.gob.ar/a5")
    monkeypatch.setenv("ALLOWED_RIVERS", "")
    strategy = INAIncrementalStrategy()
    strategy.client.get_series = MagicMock(side_effect=requests.exceptions.ConnectionError())
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    on_error.assert_called_once()
    assert on_error.call_args.kwargs["station_name"] is None
    assert stations == []
    assert measurements == []


# ─── CARU ─────────────────────────────────────────────────────────────────────

def test_caru_incremental_calls_on_error_per_station(monkeypatch):
    """Si get_station_history falla, on_error se llama con station_name."""
    from scraper.caru.strategy import CARUIncrementalStrategy

    monkeypatch.setenv("CARU_BASE_URL", "http://192.168.1.1/alturas/web/user")
    strategy = CARUIncrementalStrategy()

    stations_info = [{"name": "CONCORDIA", "caru_id": "10"}]
    strategy.client.get_main_page = MagicMock(return_value="<html></html>")
    strategy.parser.parse_main_page = MagicMock(return_value=stations_info)
    strategy.parser.stations_to_raw_data = MagicMock(return_value=[])
    strategy.client.get_station_history = MagicMock(
        side_effect=requests.exceptions.Timeout()
    )
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    on_error.assert_called_once()
    kwargs = on_error.call_args.kwargs
    assert kwargs["source"] == "CARU"
    assert kwargs["error_type"] == "TIMEOUT"
    assert kwargs["station_name"] == "CONCORDIA"
    assert measurements == []


def test_caru_main_page_failure_calls_on_error_without_station(monkeypatch):
    """Si get_main_page falla, on_error se llama sin station_name."""
    from scraper.caru.strategy import CARUIncrementalStrategy

    monkeypatch.setenv("CARU_BASE_URL", "http://192.168.1.1/alturas/web/user")
    strategy = CARUIncrementalStrategy()
    strategy.client.get_main_page = MagicMock(
        side_effect=requests.exceptions.ConnectionError("unreachable")
    )
    on_error = MagicMock()

    stations, measurements = strategy.get_data(on_error=on_error)

    on_error.assert_called_once()
    assert on_error.call_args.kwargs["station_name"] is None
    assert on_error.call_args.kwargs["source"] == "CARU"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_response(status_code: int):
    """Crea un mock de requests.Response con status_code dado."""
    r = MagicMock(spec=requests.models.Response)
    r.status_code = status_code
    return r

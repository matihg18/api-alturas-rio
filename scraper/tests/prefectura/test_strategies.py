from unittest.mock import patch, MagicMock
from scraper.prefectura.strategy import (
    PrefecturaIncrementalStrategy,
    PrefecturaBackFillStrategy,
)


# ---------------------------------------------------------------------------
# PrefecturaIncrementalStrategy
# ---------------------------------------------------------------------------

def test_incremental_fetches_detail_pages(
    html_pagina_principal, html_historico_normal, monkeypatch
):
    """La estrategia incremental debe visitar la página de detalle de cada
    estación en lugar de solo leer mapa.php."""
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    with patch("scraper.prefectura.strategy.PrefecturaClient") as MockClient:
        instance = MockClient.return_value
        # Primera llamada: página principal. Siguientes: detalle de cada estación.
        instance.fetch_data.side_effect = [
            html_pagina_principal,
            html_historico_normal,
            html_historico_normal,
        ]

        strategy = PrefecturaIncrementalStrategy(incremental_hours=48)
        stations, measurements = strategy.get_data()

    # No debe devolver estaciones (las maneja el syncer)
    assert stations == []
    # 4 de la página principal (último + anterior × 2 estaciones)
    # + 6 del histórico (3 mediciones × 2 estaciones) = 10
    assert len(measurements) == 10
    # Deben ser 3 llamadas: 1 principal + 1 por cada estación (2)
    assert instance.fetch_data.call_count == 3


def test_incremental_returns_empty_on_main_page_error(monkeypatch):
    """Si falla la página principal, debe retornar listas vacías."""
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    with patch("scraper.prefectura.strategy.PrefecturaClient") as MockClient:
        instance = MockClient.return_value
        instance.fetch_data.side_effect = Exception("connection error")

        strategy = PrefecturaIncrementalStrategy(incremental_hours=48)
        stations, measurements = strategy.get_data()

    assert stations == []
    assert measurements == []


def test_incremental_calls_on_error_when_detail_fails(
    html_pagina_principal, monkeypatch
):
    """Si falla la página de detalle de una estación, debe llamar on_error."""
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    on_error = MagicMock()

    with patch("scraper.prefectura.strategy.PrefecturaClient") as MockClient:
        instance = MockClient.return_value
        instance.fetch_data.side_effect = [
            html_pagina_principal,
            Exception("timeout"),
            Exception("timeout"),
        ]

        strategy = PrefecturaIncrementalStrategy(incremental_hours=48)
        stations, measurements = strategy.get_data(on_error=on_error)

    assert stations == []
    # Los 4 puntos recientes de la tabla principal sí se capturan
    # (la página principal cargó bien; solo fallaron los históricos).
    assert len(measurements) == 4
    # on_error se llama una vez por cada estación que falló el histórico
    assert on_error.call_count == 2


def test_incremental_hours_to_days_conversion(monkeypatch):
    """Las horas se redondean hacia arriba a días, con mínimo de 1."""
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    s1 = PrefecturaIncrementalStrategy(incremental_hours=6)
    assert s1.backfill_days == 1  # ceil(6/24) = 1

    s2 = PrefecturaIncrementalStrategy(incremental_hours=48)
    assert s2.backfill_days == 2  # ceil(48/24) = 2

    s3 = PrefecturaIncrementalStrategy(incremental_hours=36)
    assert s3.backfill_days == 2  # ceil(36/24) = 2


def test_incremental_filters_by_allowed_rivers(
    html_pagina_principal, html_historico_normal, monkeypatch
):
    """Con allowed_rivers configurado, solo se procesan las estaciones del río permitido."""
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "URUGUAY")

    with patch("scraper.prefectura.strategy.PrefecturaClient") as MockClient:
        instance = MockClient.return_value
        # La página principal tiene COLON y CONCORDIA, ambas URUGUAY: ambas pasan.
        instance.fetch_data.side_effect = [
            html_pagina_principal,
            html_historico_normal,
            html_historico_normal,
        ]

        strategy = PrefecturaIncrementalStrategy(
            incremental_hours=48, allowed_rivers=["URUGUAY"]
        )
        _, measurements = strategy.get_data()

    # Ambas estaciones son URUGUAY → 4 recientes + 6 histórico = 10
    assert len(measurements) == 10


def test_incremental_build_detail_url(monkeypatch):
    """_build_detail_url debe reemplazar el parámetro tiempo correctamente."""
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    strategy = PrefecturaIncrementalStrategy(incremental_hours=48)
    original = "https://example.com/alturas/?page=historico&tiempo=7&id=550"
    result = strategy._build_detail_url(original)

    assert "tiempo=2" in result
    assert "tiempo=7" not in result
    assert "id=550" in result


# ---------------------------------------------------------------------------
# PrefecturaBackFillStrategy (tests existentes)
# ---------------------------------------------------------------------------

def test_build_history_url_replaces_tiempo(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    strategy = PrefecturaBackFillStrategy(backfill_days=30)
    original = "https://example.com/alturas/?page=historico&tiempo=7&id=550"
    result = strategy._build_history_url(original)

    assert "tiempo=30" in result
    assert "tiempo=7" not in result
    assert "id=550" in result


def test_build_history_url_preserves_other_params(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    strategy = PrefecturaBackFillStrategy(backfill_days=90)
    original = "https://example.com/alturas/?page=historico&tiempo=7&id=100"
    result = strategy._build_history_url(original)

    assert "page=historico" in result
    assert "id=100" in result
    assert "tiempo=90" in result

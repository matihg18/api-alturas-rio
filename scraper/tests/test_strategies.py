from strategies import BackFillStrategy


def test_build_history_url_replaces_tiempo(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    strategy = BackFillStrategy(backfill_days=30)
    original = "https://example.com/alturas/?page=historico&tiempo=7&id=550"
    result = strategy._build_history_url(original)

    assert "tiempo=30" in result
    assert "tiempo=7" not in result
    assert "id=550" in result


def test_build_history_url_preserves_other_params(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    strategy = BackFillStrategy(backfill_days=90)
    original = "https://example.com/alturas/?page=historico&tiempo=7&id=100"
    result = strategy._build_history_url(original)

    assert "page=historico" in result
    assert "id=100" in result
    assert "tiempo=90" in result

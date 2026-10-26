import importlib
import scraper.config as config


def test_config_derives_base_domain(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://contenidosweb.prefecturanaval.gob.ar/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    importlib.reload(config)

    assert config.BASE_DOMAIN == "https://contenidosweb.prefecturanaval.gob.ar"
    assert config.MAP_URL == "https://contenidosweb.prefecturanaval.gob.ar/alturas/mapa.php"


def test_config_parses_allowed_rivers(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "uruguay, parana")

    importlib.reload(config)

    assert config.ALLOWED_RIVERS == ["URUGUAY", "PARANA"]


def test_config_empty_allowed_rivers(monkeypatch):
    monkeypatch.setenv("BASE_SOURCE_URL", "https://example.com/alturas/")
    monkeypatch.setenv("ALLOWED_RIVERS", "")

    importlib.reload(config)

    assert config.ALLOWED_RIVERS == []


def test_config_open_meteo_defaults(monkeypatch):
    for key in (
        "OPEN_METEO_ENABLED",
        "OPEN_METEO_INTERVAL",
        "OPEN_METEO_PAST_DAYS",
        "OPEN_METEO_ARCHIVE_DELAY_DAYS",
        "OPEN_METEO_BACKFILL_CHUNK_DAYS",
        "OPEN_METEO_MAX_POINTS_PER_REQUEST",
        "OPEN_METEO_ARCHIVE_MODEL",
        "OPEN_METEO_API_KEY",
        "OPEN_METEO_DAILY_CALL_BUDGET",
    ):
        monkeypatch.delenv(key, raising=False)

    importlib.reload(config)

    assert config.OPEN_METEO_ENABLED is True
    assert config.OPEN_METEO_INTERVAL == 3600
    assert config.OPEN_METEO_PAST_DAYS == 10
    assert config.OPEN_METEO_ARCHIVE_DELAY_DAYS == 6
    assert config.OPEN_METEO_BACKFILL_CHUNK_DAYS == 90
    assert config.OPEN_METEO_MAX_POINTS_PER_REQUEST == 50
    assert config.OPEN_METEO_ARCHIVE_MODEL == "era5"
    assert config.OPEN_METEO_API_KEY == ""
    assert config.OPEN_METEO_DAILY_CALL_BUDGET == 9000


def test_config_open_meteo_past_days_is_clamped(monkeypatch):
    monkeypatch.setenv("OPEN_METEO_PAST_DAYS", "500")

    importlib.reload(config)

    assert config.OPEN_METEO_PAST_DAYS == 92

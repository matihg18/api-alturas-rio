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

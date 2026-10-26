import os
from urllib.parse import urlparse

BASE_SOURCE_URL = os.getenv("BASE_SOURCE_URL", "")

_parsed = urlparse(BASE_SOURCE_URL)
BASE_DOMAIN = f"{_parsed.scheme}://{_parsed.netloc}" if _parsed.scheme else ""

MAP_URL = BASE_SOURCE_URL + "mapa.php"

ALLOWED_RIVERS_RAW = os.getenv("ALLOWED_RIVERS", "")
ALLOWED_RIVERS = (
    [r.strip().upper() for r in ALLOWED_RIVERS_RAW.split(",")]
    if ALLOWED_RIVERS_RAW else []
)

# Intervalos globales
SCRAPER_TICK = int(os.getenv("SCRAPER_TICK", "60"))
PREFECTURA_ENABLED = os.getenv("PREFECTURA_ENABLED", "true").lower() == "true"
PREFECTURA_INTERVAL = int(os.getenv("PREFECTURA_INTERVAL", "43200"))
PREFECTURA_INCREMENTAL_HOURS = int(os.getenv("PREFECTURA_INCREMENTAL_HOURS", "48"))

# --- INA API ---
INA_API_BASE_URL = os.getenv("INA_API_BASE_URL", "https://alerta.ina.gob.ar/a5")
INA_VAR_ID = int(os.getenv("INA_VAR_ID", "2"))  # 2 = Altura hidrométrica
INA_ENABLED = os.getenv("INA_ENABLED", "true").lower() == "true"
INA_INCREMENTAL_HOURS = int(os.getenv("INA_INCREMENTAL_HOURS", "48"))
INA_INTERVAL = int(os.getenv("INA_INTERVAL", "3600"))

# --- CARU ---
CARU_BASE_URL = os.getenv("CARU_BASE_URL", "http://190.0.152.194:8080/alturas/web/user")
CARU_ENABLED = os.getenv("CARU_ENABLED", "true").lower() == "true"
CARU_INCREMENTAL_HOURS = int(os.getenv("CARU_INCREMENTAL_HOURS", "24"))
CARU_INTERVAL = int(os.getenv("CARU_INTERVAL", "1800"))

# --- Municipalidad de Gualeguaychú ---
MUNICIPALIDAD_GCHU_URL = os.getenv(
    "MUNICIPALIDAD_GCHU_URL", "https://gualeguaychu.gov.ar/alturadelrio"
)
MUNICIPALIDAD_GCHU_ENABLED = os.getenv("MUNICIPALIDAD_GCHU_ENABLED", "true").lower() == "true"
MUNICIPALIDAD_GCHU_INTERVAL = int(os.getenv("MUNICIPALIDAD_GCHU_INTERVAL", "3600"))

# --- SGB (Servicio Geológico de Brasil) — Portal SACE ---
SGB_MAPA_URL = os.getenv(
    "SGB_MAPA_URL", "https://sace.sgb.gov.br/estacoes_mapa.php?bacia=uruguai"
)
SGB_REPORT_BASE_URL = os.getenv("SGB_REPORT_BASE_URL", "https://sace.sgb.gov.br")
SGB_ENABLED = os.getenv("SGB_ENABLED", "true").lower() == "true"
SGB_INCREMENTAL_HOURS = int(os.getenv("SGB_INCREMENTAL_HOURS", "48"))
SGB_INTERVAL = int(os.getenv("SGB_INTERVAL", "3600"))

# --- Open-Meteo (precipitación) ---
OPEN_METEO_ENABLED = os.getenv("OPEN_METEO_ENABLED", "true").lower() == "true"
OPEN_METEO_INTERVAL = int(os.getenv("OPEN_METEO_INTERVAL", "3600"))
OPEN_METEO_FORECAST_URL = os.getenv(
    "OPEN_METEO_FORECAST_URL", "https://api.open-meteo.com/v1/forecast"
)
OPEN_METEO_ARCHIVE_URL = os.getenv(
    "OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive"
)
OPEN_METEO_TIMEZONE = os.getenv(
    "OPEN_METEO_TIMEZONE", "America/Argentina/Cordoba"
)
OPEN_METEO_PAST_DAYS = max(
    1, min(92, int(os.getenv("OPEN_METEO_PAST_DAYS", "10")))
)
OPEN_METEO_ARCHIVE_DELAY_DAYS = max(
    0, int(os.getenv("OPEN_METEO_ARCHIVE_DELAY_DAYS", "6"))
)
OPEN_METEO_BACKFILL_CHUNK_DAYS = max(
    1, int(os.getenv("OPEN_METEO_BACKFILL_CHUNK_DAYS", "90"))
)
OPEN_METEO_MAX_POINTS_PER_REQUEST = max(
    1, int(os.getenv("OPEN_METEO_MAX_POINTS_PER_REQUEST", "50"))
)
OPEN_METEO_ARCHIVE_MODEL = os.getenv("OPEN_METEO_ARCHIVE_MODEL", "era5")
OPEN_METEO_API_KEY = os.getenv("OPEN_METEO_API_KEY", "")
OPEN_METEO_DAILY_CALL_BUDGET = int(
    os.getenv("OPEN_METEO_DAILY_CALL_BUDGET", "9000")
)

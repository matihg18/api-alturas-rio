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

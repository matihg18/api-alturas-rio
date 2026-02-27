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

SCRAPER_INTERVAL = int(os.getenv("SCRAPER_INTERVAL", "43200"))

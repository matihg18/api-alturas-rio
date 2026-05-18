import requests
import logging
from typing import List, Optional
from scraper.config import CARU_BASE_URL

logger = logging.getLogger(__name__)

TIMEOUT = 30


class CARUClient:
    def __init__(self, base_url: str = CARU_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        })

    def get_main_page(self) -> str:
        url = f"{self.base_url}/alturas"
        try:
            logger.info(f"CARU: fetch main page {url}")
            response = self.session.post(
                url,
                data={"form_escala": "Local"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"CARU: error fetching main page: {e}")
            return ""

    def get_station_history(self, station_id: str, days: int) -> str:
        url = f"{self.base_url}/altura/{station_id}"
        rango_tiempo = "1 Semana"
        if days > 7 and days <= 30:
            rango_tiempo = "1 Mes"
        elif days > 30 and days <= 180:
            rango_tiempo = "6 Meses"
        elif days > 180:
            rango_tiempo = "1 Año"

        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            logger.debug(f"CARU: fetch history for {station_id} (rango: {rango_tiempo})")
            response = self.session.post(
                url,
                data={"form_tiempo": rango_tiempo},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"CARU: error fetching history for {station_id}: {e}")
            return ""

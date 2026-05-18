import requests
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from scraper.config import CARU_BASE_URL

logger = logging.getLogger(__name__)

TIMEOUT = 30


class CARUClient:
    """Cliente HTTP para la página de alturas de CARU."""

    def __init__(self, base_url: str = CARU_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        # Header común para simular navegador
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        })

    def get_main_page(self) -> str:
        """
        Obtiene la página principal. Hace POST con 'form_escala=Local' 
        para asegurar que estamos en cero local.
        """
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
        """
        Obtiene la historia de una estación.
        Rango temporal en la web: '1 Semana', '1 Mes', '6 Meses', '1 Año'.
        Asignaremos el string más adecuado según 'days'.
        """
        url = f"{self.base_url}/altura/{station_id}"
        
        # Mapeo simple de days a opciones del combo
        rango_tiempo = "1 Semana"
        if days > 7 and days <= 30:
            rango_tiempo = "1 Mes"
        elif days > 30 and days <= 180:
            rango_tiempo = "6 Meses"
        elif days > 180:
            rango_tiempo = "1 Año"

        try:
            # Primero GET para obtener la página y (si hubiere) tokens CSRF/cookies
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()

            # Luego POST con el rango deseado
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

import requests
import logging
from scraper.config import CARU_BASE_URL
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 30


class CARUClient:
    def __init__(self, base_url: str = CARU_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

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
        intervalo = "0"
        if days > 7 and days <= 30:
            intervalo = "1"
        elif days > 30 and days <= 180:
            intervalo = "2"
        elif days > 180:
            intervalo = "3"

        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            token_input = soup.find("input", {"name": "form[_token]"})
            token = token_input["value"] if token_input else ""

            logger.debug(f"CARU: fetch history for {station_id} (intervalo: {intervalo})")
            payload = {
                "form[intervalo]": intervalo,
                "form[escala]": "",  # Local
                "form[_token]": token
            }
            response = self.session.post(
                url,
                data=payload,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"CARU: error fetching history for {station_id}: {e}")
            return ""

import requests
import logging

from scraper.config import SGB_MAPA_URL, SGB_REPORT_BASE_URL

logger = logging.getLogger(__name__)

TIMEOUT = 30


class SGBClient:

    def __init__(
        self,
        mapa_url: str = SGB_MAPA_URL,
        report_base_url: str = SGB_REPORT_BASE_URL,
    ):
        self.mapa_url = mapa_url
        self.report_base_url = report_base_url.rstrip("/")
        self.session = requests.Session()

    def get_stations_page(self) -> str:
        logger.info(f"SGB: fetching stations map {self.mapa_url}")
        response = self.session.get(self.mapa_url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

    def get_station_report(self, pm: str, s: str, sr: str) -> str:
        url = (
            f"{self.report_base_url}/relatorio.php"
            f"?apenas_grafico=sim&bacia=uruguai&pm={pm}&s={s}&sr={sr}"
        )
        logger.debug(f"SGB: fetching station report pm={pm} ({url})")
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

    def get_csv(self, pm: str) -> str:
        url = f"{self.report_base_url}/api/dados/uruguai_{pm}_cota.csv"
        logger.debug(f"SGB: fetching CSV for pm={pm} ({url})")
        response = self.session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

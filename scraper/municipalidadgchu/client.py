import requests
import logging

logger = logging.getLogger(__name__)

TIMEOUT = 15


class MunicipalidadGchuClient:

    def __init__(self, url: str):
        self.url = url
        self.timeout = TIMEOUT

    def fetch_page(self) -> str:
        if not self.url:
            logger.error("MUNICIPALIDAD GCHU: URL not configured")
            return ""
        logger.info(f"MUNICIPALIDAD GCHU: fetching {self.url}")
        response = requests.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

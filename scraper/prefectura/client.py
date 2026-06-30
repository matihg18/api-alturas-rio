import requests
import logging

logger = logging.getLogger(__name__)


class PrefecturaClient:
    def __init__(self):
        self.timeout = 10

    def fetch_data(self, url: str) -> str:
        if not (url):
            logger.error("URL NOT CONFIGURED")
            return ""

        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

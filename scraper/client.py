import requests
import os
import logging

logger = logging.getLogger(__name__)


class PrefecturaClient:
    def __init__(self):
        self.base_url = os.getenv("SOURCE_URL")
        self.timeout = 10
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_data(self) -> str:
        if not (self.base_url):
            logger.error("URL NOT CONFIGURED")
            return ""

        try:
            response = requests.get(
                self.base_url,
                headers = self.headers,
                timeout = self.timeout
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"ERROR FETCHING DATA: {e}")
            if 'response' in locals():
                logger.error(f"STATUS CODE: {response.status_code}")
                res_text = getattr(response, 'text', '')
                logger.error(f"RESPONSE TEXT: {str(res_text)[:200]}")
            return ""

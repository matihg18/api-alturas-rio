import requests
import os
import logging

logger = logging.getLogger(__name__)


class ScraperClient:
    def __init__(self):
        self.timeout = 10

    def fetch_data(self, url:str) -> str:
        if not (url):
            logger.error("URL NOT CONFIGURED")
            return ""

        try:
            response = requests.get(
                url,
                timeout=self.timeout
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

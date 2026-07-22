import requests
import logging
from typing import List
from scraper.config import INA_API_BASE_URL

logger = logging.getLogger(__name__)

TIMEOUT = 15
PAGE_SIZE = 200


class INAClient:
    def __init__(self, base_url: str = INA_API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_series(self, var_id: int) -> List[dict]:
        all_rows = []
        offset = 0

        while True:
            params = {
                "var_id": var_id,
                "include_geom": "false",
                "page_size": PAGE_SIZE,
                "page": offset // PAGE_SIZE,
            }
            try:
                response = self.session.get(
                    f"{self.base_url}/obs/puntual/series",
                    params=params,
                    timeout=TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
            except Exception:
                raise

            rows = data.get("rows", [])
            if not rows:
                break

            all_rows.extend(rows)

            if data.get("is_last_page", True):
                break

            offset += PAGE_SIZE

        logger.info(f"INA: {len(all_rows)} series retrieved (var_id={var_id})")
        return all_rows

    def get_observations(
        self,
        series_id: int,
        timestart: str,
        timeend: str,
    ) -> List[dict]:
        response = self.session.get(
            f"{self.base_url}/obs/puntual/series/{series_id}/observaciones",
            params={"timestart": timestart, "timeend": timeend},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

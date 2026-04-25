import requests
import logging
from typing import List, Optional
from scraper.config import INA_API_BASE_URL

logger = logging.getLogger(__name__)

TIMEOUT = 15
PAGE_SIZE = 200


class INAClient:
    """Cliente HTTP para la API REST de alerta.ina.gob.ar/a5."""

    def __init__(self, base_url: str = INA_API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_series(
        self,
        var_id: int,
        rivers: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Obtiene todas las series de la variable indicada, con paginación automática.
        Filtra por río si se provee la lista rivers.
        """
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
            except Exception as e:
                logger.error(f"INA: error fetching series (offset={offset}): {e}")
                break

            rows = data.get("rows", [])
            if not rows:
                break

            if rivers:
                normalized = [r.upper() for r in rivers]
                rows = [
                    r for r in rows
                    if ((r.get("estacion") or {}).get("rio") or "").upper() in normalized
                ]

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
        """
        Obtiene las observaciones de una serie en el rango [timestart, timeend].
        Formato de fechas: ISO 8601 (e.g. '2026-04-17T00:00:00Z').
        """
        try:
            response = self.session.get(
                f"{self.base_url}/obs/puntual/series/{series_id}/observaciones",
                params={"timestart": timestart, "timeend": timeend},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"INA: error fetching observations for series {series_id}: {e}")
            return []

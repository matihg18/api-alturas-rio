import logging
from datetime import date
from typing import Any

import requests

import scraper.config as config
from scraper.schemas import PrecipitationPoint

logger = logging.getLogger(__name__)

TIMEOUT = 30


class OpenMeteoClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    @staticmethod
    def _chunks(
        points: list[PrecipitationPoint],
        size: int,
    ) -> list[list[PrecipitationPoint]]:
        return [points[i:i + size] for i in range(0, len(points), size)]

    def _base_params(self, points: list[PrecipitationPoint]) -> dict[str, Any]:
        params: dict[str, Any] = {
            "latitude": ",".join(str(point.latitud) for point in points),
            "longitude": ",".join(str(point.longitud) for point in points),
            "hourly": "precipitation",
            "precipitation_unit": "mm",
            "timezone": config.OPEN_METEO_TIMEZONE,
            "cell_selection": "land",
        }
        if config.OPEN_METEO_API_KEY:
            params["apikey"] = config.OPEN_METEO_API_KEY
        return params

    def _get(self, url: str, params: dict[str, Any]) -> Any:
        response = self.session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ValueError(data.get("reason", "Open-Meteo error"))
        return data

    def get_forecast(
        self,
        points: list[PrecipitationPoint],
        past_days: int,
    ) -> list[dict]:
        results: list[dict] = []
        for chunk in self._chunks(points, config.OPEN_METEO_MAX_POINTS_PER_REQUEST):
            params = self._base_params(chunk)
            params["past_days"] = past_days
            params["forecast_days"] = 1
            data = self._get(config.OPEN_METEO_FORECAST_URL, params)
            results.extend(data if isinstance(data, list) else [data])
        return results

    def get_archive(
        self,
        points: list[PrecipitationPoint],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        results: list[dict] = []
        for chunk in self._chunks(points, config.OPEN_METEO_MAX_POINTS_PER_REQUEST):
            params = self._base_params(chunk)
            params["start_date"] = start_date.isoformat()
            params["end_date"] = end_date.isoformat()
            if config.OPEN_METEO_ARCHIVE_MODEL:
                params["models"] = config.OPEN_METEO_ARCHIVE_MODEL
            data = self._get(config.OPEN_METEO_ARCHIVE_URL, params)
            results.extend(data if isinstance(data, list) else [data])
        return results

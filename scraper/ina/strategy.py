import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional

from scraper.base import ScraperStrategy, OnErrorCallback
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.ina.client import INAClient
from scraper.ina.parser import INAParser
from scraper.errors import classify_error
from scraper.utils import is_river_allowed, normalize_river
import scraper.config as config

logger = logging.getLogger(__name__)

SOURCE_NAME = "INA"


def _get_data(
    client: INAClient,
    parser: INAParser,
    timestart: str,
    timeend: str,
    allowed_rivers: list[str],
    on_error: OnErrorCallback = None,
) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
    try:
        series_list = client.get_series(var_id=config.INA_VAR_ID)
    except Exception as e:
        logger.error(f"INA: failed to fetch series list: {e}")
        if on_error:
            error_type, status = classify_error(e)
            on_error(
                source=SOURCE_NAME,
                error_type=error_type,
                error_message=str(e),
                station_name=None,
                url=f"{config.INA_API_BASE_URL}/obs/puntual/series",
                http_status_code=status,
            )
        return [], []

    # Filtrar por río antes de hacer requests por estación.
    # Lista vacía = sin filtro (acepta todas las series).
    if allowed_rivers:
        def _passes_river_filter(s: dict) -> bool:
            estacion = s.get("estacion") or {}
            rio = estacion.get("rio") or ""
            if rio:
                # Caso normal: el campo río está poblado.
                return is_river_allowed(rio, allowed_rivers)
            # Fallback: río ausente → solo aceptar si el nombre de la estación
            # EMPIEZA con el nombre de un río permitido (convención del INA:
            # "Gualeguaychú - RN Nº 130", "Uruguay - El Soberbio", etc.).
            nombre = normalize_river(estacion.get("nombre") or "")
            return any(
                nombre.startswith(normalize_river(r))
                for r in allowed_rivers
                if r
            )

        series_list = [s for s in series_list if _passes_river_filter(s)]
        logger.info(f"INA: {len(series_list)} series after river filter {allowed_rivers}")

    stations = parser.parse_series(series_list)

    # --- Request por estación ---
    all_measurements: List[RawMeasurementData] = []
    for serie in series_list:
        series_id = serie.get("id")
        estacion = serie.get("estacion") or {}
        station_name = estacion.get("nombre", "").strip()

        if not series_id or not station_name:
            continue

        obs_url = f"{config.INA_API_BASE_URL}/obs/puntual/series/{series_id}/observaciones"
        logger.info(f"INA: fetching history for '{station_name}'")
        try:
            obs = client.get_observations(series_id, timestart, timeend)
            measurements = parser.parse_observations(obs, station_name)
            logger.info(f"  -> {len(measurements)} valid observations found")
            all_measurements.extend(measurements)
        except Exception as e:
            logger.error(f"INA: error fetching observations for '{station_name}': {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=station_name,
                    url=obs_url,
                    http_status_code=status,
                )

    return stations, all_measurements


class INAIncrementalStrategy(ScraperStrategy):

    def __init__(self, allowed_rivers: Optional[list[str]] = None):
        self.client = INAClient()
        self.parser = INAParser()
        self.allowed_rivers = [normalize_river(r) for r in (allowed_rivers or [])]

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        now = datetime.now(timezone.utc)
        timeend = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        timestart = (now - timedelta(hours=config.INA_INCREMENTAL_HOURS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return _get_data(self.client, self.parser, timestart, timeend, self.allowed_rivers, on_error)


class INABackFillStrategy(ScraperStrategy):

    def __init__(self, backfill_days: int, allowed_rivers: Optional[list[str]] = None):
        self.client = INAClient()
        self.parser = INAParser()
        self.backfill_days = backfill_days
        self.allowed_rivers = [normalize_river(r) for r in (allowed_rivers or [])]

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        now = datetime.now(timezone.utc)
        timeend = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        timestart = (now - timedelta(days=self.backfill_days)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return _get_data(self.client, self.parser, timestart, timeend, self.allowed_rivers, on_error)

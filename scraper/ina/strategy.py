import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from scraper.base import ScraperStrategy, OnErrorCallback
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.ina.client import INAClient
from scraper.ina.parser import INAParser
from scraper.errors import classify_error
import scraper.config as config

logger = logging.getLogger(__name__)

SOURCE_NAME = "INA"


def _get_data(
    client: INAClient,
    parser: INAParser,
    timestart: str,
    timeend: str,
    on_error: OnErrorCallback = None,
) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
    """Lógica compartida entre Incremental y BackFill."""

    # --- Request de descubrimiento: lista de series ---
    try:
        series_list = client.get_series(
            var_id=config.INA_VAR_ID,
            rivers=config.ALLOWED_RIVERS or None,
        )
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
    """
    Obtiene las series de altura hidrométrica del INA para los ríos en
    ALLOWED_RIVERS y descarga las observaciones de las últimas
    INA_INCREMENTAL_HOURS horas.
    """

    def __init__(self):
        self.client = INAClient()
        self.parser = INAParser()

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        now = datetime.now(timezone.utc)
        timeend = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        timestart = (now - timedelta(hours=config.INA_INCREMENTAL_HOURS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return _get_data(self.client, self.parser, timestart, timeend, on_error)


class INABackFillStrategy(ScraperStrategy):
    """
    Igual que INAIncrementalStrategy pero con una ventana temporal de
    backfill_days días hacia atrás.
    """

    def __init__(self, backfill_days: int):
        self.client = INAClient()
        self.parser = INAParser()
        self.backfill_days = backfill_days

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        now = datetime.now(timezone.utc)
        timeend = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        timestart = (now - timedelta(days=self.backfill_days)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return _get_data(self.client, self.parser, timestart, timeend, on_error)

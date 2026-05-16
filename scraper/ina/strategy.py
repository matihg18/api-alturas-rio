import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from scraper.base import ScraperStrategy
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.ina.client import INAClient
from scraper.ina.parser import INAParser
import scraper.config as config

logger = logging.getLogger(__name__)


class INAIncrementalStrategy(ScraperStrategy):
    """
    Obtiene las series de altura hidrométrica del INA para los ríos en
    ALLOWED_RIVERS y descarga las observaciones de las últimas
    INA_INCREMENTAL_HOURS horas.
    """

    def __init__(self):
        self.client = INAClient()
        self.parser = INAParser()

    def get_data(self) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        now = datetime.now(timezone.utc)
        timeend = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        timestart = (now - timedelta(hours=config.INA_INCREMENTAL_HOURS)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        series_list = self.client.get_series(
            var_id=config.INA_VAR_ID,
            rivers=config.ALLOWED_RIVERS or None,
        )

        stations = self.parser.parse_series(series_list)

        all_measurements: List[RawMeasurementData] = []
        for serie in series_list:
            series_id = serie.get("id")
            estacion = serie.get("estacion") or {}
            station_name = estacion.get("nombre", "").strip()

            if not series_id or not station_name:
                continue

            logger.info(
                f"INA: fetching observations for '{station_name}' "
                f"({timestart} → {timeend})"
            )
            obs = self.client.get_observations(series_id, timestart, timeend)
            measurements = self.parser.parse_observations(obs, station_name)
            logger.info(f"  -> {len(measurements)} observations")
            all_measurements.extend(measurements)

        return stations, all_measurements


class INABackFillStrategy(ScraperStrategy):
    """
    Igual que INAIncrementalStrategy pero con una ventana temporal de
    backfill_days días hacia atrás.
    """

    def __init__(self, backfill_days: int):
        self.client = INAClient()
        self.parser = INAParser()
        self.backfill_days = backfill_days

    def get_data(self) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        now = datetime.now(timezone.utc)
        timeend = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        timestart = (now - timedelta(days=self.backfill_days)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        series_list = self.client.get_series(
            var_id=config.INA_VAR_ID,
            rivers=config.ALLOWED_RIVERS or None,
        )

        stations = self.parser.parse_series(series_list)

        all_measurements: List[RawMeasurementData] = []
        for serie in series_list:
            series_id = serie.get("id")
            estacion = serie.get("estacion") or {}
            station_name = estacion.get("nombre", "").strip()

            if not series_id or not station_name:
                continue

            logger.info(
                f"INA: fetching {self.backfill_days}d history for '{station_name}'"
            )
            obs = self.client.get_observations(series_id, timestart, timeend)
            measurements = self.parser.parse_observations(obs, station_name)
            logger.info(f"  -> {len(measurements)} observations")
            all_measurements.extend(measurements)

        return stations, all_measurements

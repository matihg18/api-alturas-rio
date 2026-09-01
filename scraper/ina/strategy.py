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
        series_list = [
            s for s in series_list
            if is_river_allowed((s.get("estacion") or {}).get("rio") or "", allowed_rivers)
        ]
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


BACKFILL_CHUNK_DAYS = 30  # Ventana máxima por request. INA hace timeout con rangos muy grandes
                          # en estaciones con mediciones horarias (~8760 obs para 365 días).


class INABackFillStrategy(ScraperStrategy):

    def __init__(self, backfill_days: int, allowed_rivers: Optional[list[str]] = None):
        self.client = INAClient()
        self.parser = INAParser()
        self.backfill_days = backfill_days
        self.allowed_rivers = [normalize_river(r) for r in (allowed_rivers or [])]

    def _build_chunks(self) -> List[Tuple[str, str]]:
        """Divide el rango total en ventanas de BACKFILL_CHUNK_DAYS días.

        Retorna lista de (timestart, timeend) en orden cronológico ascendente.
        """
        now = datetime.now(timezone.utc)
        chunks = []
        chunk_end = now
        while True:
            chunk_start = chunk_end - timedelta(days=BACKFILL_CHUNK_DAYS)
            total_start = now - timedelta(days=self.backfill_days)
            if chunk_start <= total_start:
                chunk_start = total_start
                chunks.append((
                    chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                ))
                break
            chunks.append((
                chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ))
            chunk_end = chunk_start
        return list(reversed(chunks))

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        chunks = self._build_chunks()
        n_chunks = len(chunks)
        logger.info(
            f"INA BACKFILL: {self.backfill_days} days split into {n_chunks} chunks "
            f"of up to {BACKFILL_CHUNK_DAYS} days each"
        )

        all_stations: List[RawStationData] = []
        all_measurements: List[RawMeasurementData] = []

        for i, (timestart, timeend) in enumerate(chunks, start=1):
            logger.info(f"INA BACKFILL: chunk {i}/{n_chunks} [{timestart} → {timeend}]")
            stations, measurements = _get_data(
                self.client, self.parser, timestart, timeend, self.allowed_rivers, on_error
            )
            # Las estaciones son las mismas en todos los chunks; basta con el primero.
            if i == 1:
                all_stations = stations
            all_measurements.extend(measurements)

        return all_stations, all_measurements


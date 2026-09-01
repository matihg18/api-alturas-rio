import math
import re
import time
import logging
from typing import List, Tuple
from scraper.prefectura.client import PrefecturaClient
from scraper.prefectura.parser import PrefecturaBackFillParser
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.config import BASE_SOURCE_URL, BASE_DOMAIN
from scraper.errors import classify_error
from scraper.base import OnErrorCallback, ScraperStrategy
from scraper.utils import is_river_allowed, normalize_river

logger = logging.getLogger(__name__)

SOURCE_NAME = "Prefectura"


class PrefecturaIncrementalStrategy(ScraperStrategy):
    def __init__(self, incremental_hours: int = 48, allowed_rivers: list[str] | None = None):
        self.client = PrefecturaClient()
        self.parser = PrefecturaBackFillParser(BASE_DOMAIN)
        self.backfill_days = max(1, math.ceil(incremental_hours / 24))
        self.url = BASE_SOURCE_URL
        self.allowed_rivers = [normalize_river(r) for r in (allowed_rivers or [])]

    def _build_detail_url(self, original_url: str) -> str:
        return re.sub(r'tiempo=\d+', f'tiempo={self.backfill_days}', original_url)

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        try:
            raw_data = self.client.fetch_data(self.url)
        except Exception as e:
            logger.error(f"PREFECTURA INCREMENTAL: failed to fetch main page: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=self.url,
                    http_status_code=status,
                )
            return [], []

        ports = self.parser.parse_port_urls(raw_data)
        logger.info(f"PREFECTURA: found {len(ports)} stations (last {self.backfill_days * 24}h)")

        # Captura Último Registro y Registro Anterior de la tabla principal.
        # Cubre el lag del histórico: los puntos más recientes solo aparecen aquí
        # hasta que Prefectura actualice la página de detalle. El repositorio
        # deduplica por (station_id, date_time), así que no hay riesgo de duplicados.
        all_measurements: List[RawMeasurementData] = self.parser.parse_recent_measurements(raw_data)
        logger.info(f"  -> {len(all_measurements)} recent measurements from main page")

        for port in ports:
            if self.allowed_rivers and not is_river_allowed(port['river'], self.allowed_rivers):
                continue

            detail_url = self._build_detail_url(port['history_url'])
            logger.info(f"PREFECTURA: fetching history for '{port['name']}' (last {self.backfill_days * 24}h)")
            try:
                raw_detail = self.client.fetch_data(detail_url)
                data = self.parser.parse_history_table(raw_detail, port['name'])
                logger.info(f"  -> {len(data)} valid observations found")
                all_measurements.extend(data)
            except Exception as e:
                logger.error(
                    f"PREFECTURA: error fetching history for '{port['name']}': {e}"
                )
                if on_error:
                    error_type, status = classify_error(e)
                    on_error(
                        source=SOURCE_NAME,
                        error_type=error_type,
                        error_message=str(e),
                        station_name=port['name'],
                        url=detail_url,
                        http_status_code=status,
                    )
            finally:
                # Delay para evitar rate limiting del servidor de Prefectura.
                time.sleep(0.5)

        # Las estaciones se sincronizan desde PrefecturaStationSyncer (mapa.php).
        return [], all_measurements


class PrefecturaBackFillStrategy(ScraperStrategy):
    def __init__(self, backfill_days: int, allowed_rivers: list[str] | None = None):
        self.client = PrefecturaClient()
        self.parser = PrefecturaBackFillParser(BASE_DOMAIN)
        self.backfill_days = backfill_days
        self.url = BASE_SOURCE_URL
        self.allowed_rivers = [normalize_river(r) for r in (allowed_rivers or [])]

    def _build_history_url(self, original_url: str) -> str:
        return re.sub(r'tiempo=\d+', f'tiempo={self.backfill_days}', original_url)

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        try:
            raw_data = self.client.fetch_data(self.url)
        except Exception as e:
            logger.error(f"PREFECTURA BACKFILL: failed to fetch main page: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=self.url,
                    http_status_code=status,
                )
            return [], []

        ports = self.parser.parse_port_urls(raw_data)
        logger.info(f"PREFECTURA: found {len(ports)} stations with history URLs")

        all_measurements: List[RawMeasurementData] = []

        for port in ports:
            if self.allowed_rivers and not is_river_allowed(port['river'], self.allowed_rivers):
                continue

            history_url = self._build_history_url(port['history_url'])
            logger.info(
                f"PREFECTURA: fetching history for '{port['name']}' (last {self.backfill_days * 24}h)"
            )
            try:
                raw_history = self.client.fetch_data(history_url)
                data = self.parser.parse_history_table(raw_history, port['name'])
                logger.info(f"  -> {len(data)} valid observations found")
                all_measurements.extend(data)
            except Exception as e:
                logger.error(f"PREFECTURA BACKFILL: error for station '{port['name']}': {e}")
                if on_error:
                    error_type, status = classify_error(e)
                    on_error(
                        source=SOURCE_NAME,
                        error_type=error_type,
                        error_message=str(e),
                        station_name=port['name'],
                        url=history_url,
                        http_status_code=status,
                    )
            finally:
                # Delay para evitar rate limiting del servidor de Prefectura.
                # Sin esto, 90 requests en ráfaga provoca 403/SSL errors a partir de la estación ~25.
                time.sleep(1.5)

        return [], all_measurements

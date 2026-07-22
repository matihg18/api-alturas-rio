import logging
from typing import List, Tuple

from scraper.base import ScraperStrategy, OnErrorCallback
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.municipalidadgchu.client import MunicipalidadGchuClient
from scraper.municipalidadgchu.parser import MunicipalidadGchuParser
from scraper.errors import classify_error
import scraper.config as config

logger = logging.getLogger(__name__)

SOURCE_NAME = "Municipalidad Gualeguaychú"


class MunicipalidadGchuIncrementalStrategy(ScraperStrategy):
    """Obtiene la medición actual de la página de la Municipalidad de Gualeguaychú."""

    def __init__(self):
        self.client = MunicipalidadGchuClient(config.MUNICIPALIDAD_GCHU_URL)
        self.parser = MunicipalidadGchuParser()

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        url = config.MUNICIPALIDAD_GCHU_URL
        try:
            html = self.client.fetch_page()
            return self.parser.parse_current(html)
        except Exception as e:
            logger.error(f"MUNICIPALIDAD GCHU INCREMENTAL: failed to fetch/parse data: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=url,
                    http_status_code=status,
                )
            return [], []


class MunicipalidadGchuBackFillStrategy(ScraperStrategy):
    """Carga el historial de los últimos 3 días embebido en la página de la Municipalidad."""

    def __init__(self, backfill_days: int):
        self.client = MunicipalidadGchuClient(config.MUNICIPALIDAD_GCHU_URL)
        self.parser = MunicipalidadGchuParser()
        # La página sólo expone ~3 días de historial; si se piden más, se usa el máximo disponible
        self.hours = min(backfill_days * 24, 72)

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        url = config.MUNICIPALIDAD_GCHU_URL
        try:
            html = self.client.fetch_page()
            return self.parser.parse_history(html, since_hours=self.hours)
        except Exception as e:
            logger.error(f"MUNICIPALIDAD GCHU BACKFILL: failed to fetch/parse data: {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=None,
                    url=url,
                    http_status_code=status,
                )
            return [], []

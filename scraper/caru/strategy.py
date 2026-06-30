import logging
from typing import List, Tuple, Optional

from scraper.base import ScraperStrategy, OnErrorCallback
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.caru.client import CARUClient
from scraper.caru.parser import CARUParser
from scraper.errors import classify_error
import scraper.config as config

logger = logging.getLogger(__name__)

SOURCE_NAME = "CARU"


class CARUIncrementalStrategy(ScraperStrategy):
    def __init__(self):
        self.client = CARUClient()
        self.parser = CARUParser()
        self.hours = config.CARU_INCREMENTAL_HOURS

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        return _fetch_caru_data(self.client, self.parser, self.hours, on_error)


class CARUBackFillStrategy(ScraperStrategy):
    def __init__(self, backfill_days: int):
        self.client = CARUClient()
        self.parser = CARUParser()
        self.hours = backfill_days * 24

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        return _fetch_caru_data(self.client, self.parser, self.hours, on_error)


def _fetch_caru_data(
    client: CARUClient,
    parser: CARUParser,
    hours: int,
    on_error: OnErrorCallback = None,
) -> Tuple[List[RawStationData], List[RawMeasurementData]]:

    # --- Request de descubrimiento: página principal ---
    main_url = f"{config.CARU_BASE_URL}/alturas"
    try:
        main_html = client.get_main_page()
    except Exception as e:
        logger.error(f"CARU: failed to fetch main page: {e}")
        if on_error:
            error_type, status = classify_error(e)
            on_error(
                source=SOURCE_NAME,
                error_type=error_type,
                error_message=str(e),
                station_name=None,
                url=main_url,
                http_status_code=status,
            )
        return [], []

    stations_info = parser.parse_main_page(main_html)
    logger.info(f"CARU: found {len(stations_info)} stations on main page")
    stations = parser.stations_to_raw_data(stations_info)

    # --- Request por estación ---
    all_measurements = []
    for info in stations_info:
        station_name = info["name"]
        caru_id = info["caru_id"]
        station_url = f"{config.CARU_BASE_URL}/altura/{caru_id}"
        logger.info(f"CARU: fetching history for '{station_name}' (last {hours}h)")
        try:
            history_html = client.get_station_history(caru_id, days=max(1, hours // 24))
            measurements = parser.parse_history(history_html, station_name, since_hours=hours)
            logger.info(f"  -> {len(measurements)} valid observations found")
            all_measurements.extend(measurements)
        except Exception as e:
            logger.error(f"CARU: error fetching history for '{station_name}': {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=station_name,
                    url=station_url,
                    http_status_code=status,
                )

    return stations, all_measurements

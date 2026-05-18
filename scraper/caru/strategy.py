import logging
from typing import List, Tuple

from scraper.base import ScraperStrategy
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.caru.client import CARUClient
from scraper.caru.parser import CARUParser
import scraper.config as config

logger = logging.getLogger(__name__)


class CARUIncrementalStrategy(ScraperStrategy):
    def __init__(self):
        self.client = CARUClient()
        self.parser = CARUParser()
        self.hours = config.CARU_INCREMENTAL_HOURS

    def get_data(self) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        return _fetch_caru_data(self.client, self.parser, self.hours)


class CARUBackFillStrategy(ScraperStrategy):
    def __init__(self, backfill_days: int):
        self.client = CARUClient()
        self.parser = CARUParser()
        self.hours = backfill_days * 24

    def get_data(self) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        return _fetch_caru_data(self.client, self.parser, self.hours)


def _fetch_caru_data(
    client: CARUClient, parser: CARUParser, hours: int
) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
    main_html = client.get_main_page()
    if not main_html:
        return [], []
    stations_info = parser.parse_main_page(main_html)
    logger.info(f"CARU: found {len(stations_info)} stations on main page")
    stations = parser.stations_to_raw_data(stations_info)
    all_measurements = []
    for info in stations_info:
        station_name = info["name"]
        caru_id = info["caru_id"]
        logger.info(f"CARU: fetching history for '{station_name}' (last {hours}h)")
        history_html = client.get_station_history(caru_id, days=max(1, hours // 24))
        if history_html:
            measurements = parser.parse_history(history_html, station_name, since_hours=hours)
            logger.info(f"  -> {len(measurements)} valid observations found")
            all_measurements.extend(measurements)
    return stations, all_measurements

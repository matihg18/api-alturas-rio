import logging
from typing import List, Tuple

from scraper.base import ScraperStrategy, OnErrorCallback
from scraper.schemas import RawStationData, RawMeasurementData
from scraper.sgb.client import SGBClient
from scraper.sgb.parser import SGBParser
from scraper.errors import classify_error
import scraper.config as config

logger = logging.getLogger(__name__)

SOURCE_NAME = "SGB"


def _fetch_sgb_data(
    client: SGBClient,
    parser: SGBParser,
    hours: int,
    on_error: OnErrorCallback = None,
) -> Tuple[List[RawStationData], List[RawMeasurementData]]:

    mapa_url = config.SGB_MAPA_URL
    try:
        mapa_html = client.get_stations_page()
    except Exception as e:
        logger.error(f"SGB: failed to fetch stations map: {e}")
        if on_error:
            error_type, status = classify_error(e)
            on_error(
                source=SOURCE_NAME,
                error_type=error_type,
                error_message=str(e),
                station_name=None,
                url=mapa_url,
                http_status_code=status,
            )
        return [], []

    stations_info = parser.parse_stations_page(mapa_html)
    if not stations_info:
        logger.warning("SGB: no stations found in map page")
        return [], []

    all_measurements: List[RawMeasurementData] = []
    raw_stations: List[RawStationData] = []

    for info in stations_info:
        pm = info["pm"]
        s = info["s"]
        sr = info["sr"]
        station_name = info["name"]

        report_url = (
            f"{config.SGB_REPORT_BASE_URL}/relatorio.php"
            f"?apenas_grafico=sim&bacia=uruguai&pm={pm}&s={s}&sr={sr}"
        )
        try:
            report_html = client.get_station_report(pm, s, sr)
            river = parser.parse_river_from_report(report_html)
        except Exception as e:
            logger.warning(
                f"SGB: could not fetch report for '{station_name}' (pm={pm}): {e}. "
                "Using fallback river name."
            )
            river = info["river"] 

        info["river"] = river
        raw_stations.append(parser.station_to_raw_data(info))

        csv_url = f"{config.SGB_REPORT_BASE_URL}/api/dados/uruguai_{pm}_cota.csv"
        logger.info(f"SGB: fetching CSV for '{station_name}' (pm={pm}, last {hours}h)")
        try:
            csv_text = client.get_csv(pm)
            measurements = parser.parse_csv(csv_text, station_name, river, since_hours=hours)
            logger.info(f"  -> {len(measurements)} valid observations found")
            all_measurements.extend(measurements)
        except Exception as e:
            logger.error(f"SGB: error fetching CSV for '{station_name}' (pm={pm}): {e}")
            if on_error:
                error_type, status = classify_error(e)
                on_error(
                    source=SOURCE_NAME,
                    error_type=error_type,
                    error_message=str(e),
                    station_name=station_name,
                    url=csv_url,
                    http_status_code=status,
                )

    return raw_stations, all_measurements


class SGBIncrementalStrategy(ScraperStrategy):

    def __init__(self):
        self.client = SGBClient()
        self.parser = SGBParser()
        self.hours = config.SGB_INCREMENTAL_HOURS

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        return _fetch_sgb_data(self.client, self.parser, self.hours, on_error)


class SGBBackFillStrategy(ScraperStrategy):

    def __init__(self, backfill_days: int):
        self.client = SGBClient()
        self.parser = SGBParser()
        self.hours = backfill_days * 24

    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        return _fetch_sgb_data(self.client, self.parser, self.hours, on_error)

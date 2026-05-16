import logging
from scraper.prefectura.client import PrefecturaClient
from scraper.prefectura.parser import PrefecturaIncrementalParser
from scraper.schemas import RawStationData
from scraper.config import MAP_URL
from typing import List
from scraper.base import BaseStationSyncer

logger = logging.getLogger(__name__)


class PrefecturaStationSyncer(BaseStationSyncer):

    def __init__(self):
        self.client = PrefecturaClient()
        self.parser = PrefecturaIncrementalParser()
        self.url = MAP_URL

    def sync(self) -> List[RawStationData]:
        raw_data = self.client.fetch_data(self.url)
        stations, _ = self.parser.parse(raw_data)
        logger.info(f"{len(stations)} stations obtained from mapa.php")
        return stations

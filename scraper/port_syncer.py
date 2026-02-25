import logging
from client import ScraperClient
from parser import IncrementalParser, RawPortData
from config import MAP_URL
from typing import List

logger = logging.getLogger(__name__)


class PortSyncer:

    def __init__(self):
        self.client = ScraperClient()
        self.parser = IncrementalParser()
        self.url = MAP_URL

    def sync(self) -> List[RawPortData]:
        raw_data = self.client.fetch_data(self.url)
        ports, _ = self.parser.parse(raw_data)
        logger.info(f"{len(ports)} ports obtained from mapa.php")
        return ports

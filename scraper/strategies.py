from abc import ABC, abstractmethod
from typing import List, Tuple
from client import ScraperClient
from parser import (
    RawPortData,
    RawMeasurementData,
    IncrementalParser,
    BackFillParser,
)
from config import MAP_URL, BASE_SOURCE_URL, BASE_DOMAIN, ALLOWED_RIVERS
import re
import logging

logger = logging.getLogger(__name__)


class ScraperStrategy(ABC):
    @abstractmethod
    def get_data(self) -> Tuple[List[RawPortData], List[RawMeasurementData]]:
        pass


class IncrementalStrategy(ScraperStrategy):
    def __init__(self):
        self.client = ScraperClient()
        self.parser = IncrementalParser()
        self.url = MAP_URL

    def get_data(self) -> Tuple[List[RawPortData], List[RawMeasurementData]]:
        raw_data = self.client.fetch_data(self.url)
        return self.parser.parse(raw_data)


class BackFillStrategy(ScraperStrategy):
    def __init__(self, backfill_days: int):
        self.client = ScraperClient()
        self.parser = BackFillParser(BASE_DOMAIN)
        self.backfill_days = backfill_days
        self.url = BASE_SOURCE_URL
        self.allowed_rivers = ALLOWED_RIVERS

    def _build_history_url(self, original_url: str) -> str:
        return re.sub(r'tiempo=\d+', f'tiempo={self.backfill_days}', original_url)

    def get_data(self) -> Tuple[List[RawPortData], List[RawMeasurementData]]:
        raw_data = self.client.fetch_data(self.url)
        ports = self.parser.parse_port_urls(raw_data)
        logger.info(f"Found {len(ports)} ports with history URLs")

        all_measurements: List[RawMeasurementData] = []

        for port in ports:
            if self.allowed_rivers and port['river'] not in self.allowed_rivers:
                continue

            history_url = self._build_history_url(port['history_url'])
            logger.info(f"Fetching history for {port['name']} ({self.backfill_days} days)")
            raw_history = self.client.fetch_data(history_url)
            data = self.parser.parse_history_table(raw_history, port['name'])
            logger.info(f"  -> {len(data)} measurements found")
            all_measurements.extend(data)

        return [], all_measurements

from abc import ABC, abstractmethod
from typing import List, Tuple
from scraper.schemas import RawStationData, RawMeasurementData


class ScraperStrategy(ABC):
    @abstractmethod
    def get_data(self) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        pass


class BaseStationSyncer(ABC):
    @abstractmethod
    def sync(self) -> List[RawStationData]:
        pass

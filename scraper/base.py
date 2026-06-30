from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Optional
from scraper.schemas import RawStationData, RawMeasurementData


# Tipo del callback de errores que se inyecta en get_data().
# Firma: on_error(source, error_type, error_message, station_name, url, http_status_code)
OnErrorCallback = Optional[Callable[..., None]]


class ScraperStrategy(ABC):
    @abstractmethod
    def get_data(
        self,
        on_error: OnErrorCallback = None,
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        pass


class BaseStationSyncer(ABC):
    @abstractmethod
    def sync(self) -> List[RawStationData]:
        pass

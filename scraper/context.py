import logging
from typing import Optional
from scraper.base import ScraperStrategy, BaseStationSyncer
from scraper.repository import ScraperRepository
from scraper.schemas import RawStationData
from scraper.utils import is_river_allowed, normalize_river

logger = logging.getLogger(__name__)


class ScraperContext:
    def __init__(
        self,
        strategy: ScraperStrategy,
        station_syncer: BaseStationSyncer,
        repository: ScraperRepository,
        allowed_rivers: Optional[list[str]] = None,
    ):
        self.strategy = strategy
        self.station_syncer = station_syncer
        self.repository = repository
        self.allowed_rivers = [normalize_river(r) for r in (allowed_rivers or [])]

    def _filter_stations(self, stations: list[RawStationData]) -> list[RawStationData]:
        if not self.allowed_rivers:
            return stations
        filtered = [s for s in stations if is_river_allowed(s.river, self.allowed_rivers)]
        skipped = len(stations) - len(filtered)
        if skipped:
            logger.debug(f"Filtered out {skipped} station(s) not in allowed rivers.")
        return filtered

    def execute(self):
        logger.info("=== PHASE 1: Synchronizing stations ===")
        station_data = self._filter_stations(self.station_syncer.sync())
        self.repository.sync_stations(station_data)

        logger.info("=== PHASE 2: Collecting measurements ===")
        stations, measurements = self.strategy.get_data(on_error=self.repository.log_error)
        if stations:
            self.repository.sync_stations(self._filter_stations(stations))

        self.repository.save_measurements(measurements)
        logger.info("=== Execution completed ===")

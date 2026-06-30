import logging
from scraper.base import ScraperStrategy, BaseStationSyncer
from scraper.repository import ScraperRepository

logger = logging.getLogger(__name__)


class ScraperContext:
    def __init__(
        self,
        strategy: ScraperStrategy,
        station_syncer: BaseStationSyncer,
        repository: ScraperRepository,
    ):
        self.strategy = strategy
        self.station_syncer = station_syncer
        self.repository = repository

    def execute(self):
        logger.info("=== PHASE 1: Synchronizing stations ===")
        station_data = self.station_syncer.sync()
        self.repository.sync_stations(station_data)

        logger.info("=== PHASE 2: Collecting measurements ===")
        stations, measurements = self.strategy.get_data(on_error=self.repository.log_error)
        if stations:
            self.repository.sync_stations(stations)

        self.repository.save_measurements(measurements)
        logger.info("=== Execution completed ===")

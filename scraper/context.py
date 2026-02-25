import logging
from strategies import ScraperStrategy
from port_syncer import PortSyncer
from repository import ScraperRepository

logger = logging.getLogger(__name__)


class ScraperContext:
    def __init__(
        self,
        strategy: ScraperStrategy,
        port_syncer: PortSyncer,
        repository: ScraperRepository,
    ):
        self.strategy = strategy
        self.port_syncer = port_syncer
        self.repository = repository

    def execute(self):
        logger.info("=== PHASE 1: Synchronizing ports ===")
        port_data = self.port_syncer.sync()
        self.repository.sync_ports(port_data)

        logger.info("=== PHASE 2: Collecting measurements ===")
        ports, measurements = self.strategy.get_data()
        if ports:
            self.repository.sync_ports(ports)

        self.repository.save_measurements(measurements)
        logger.info("=== Execution completed ===")
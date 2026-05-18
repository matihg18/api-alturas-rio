import os
import time
import logging
from dataclasses import dataclass

from scraper.prefectura.strategy import PrefecturaIncrementalStrategy, PrefecturaBackFillStrategy
from scraper.ina.strategy import INAIncrementalStrategy, INABackFillStrategy
from scraper.prefectura.syncer import PrefecturaStationSyncer
from scraper.repository import ScraperRepository
from scraper.context import ScraperContext
import scraper.config as config
from common.database import SessionLocal, engine
from common.models import Base
from scraper.base import BaseStationSyncer

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


class NoOpStationSyncer(BaseStationSyncer):
    """Syncer vacío para estrategias que manejan su propio sync de estaciones."""

    def sync(self):
        return []


@dataclass
class SourceRunner:
    name: str
    context: ScraperContext
    interval: int          # segundos
    last_run: float = 0.0  # timestamp epoch

    def is_due(self) -> bool:
        return time.time() - self.last_run >= self.interval

    def run(self):
        logger.info(f"=== Running source: {self.name} ===")
        try:
            self.context.execute()
        except Exception as e:
            logger.error(f"Source {self.name} failed: {e}", exc_info=True)
        finally:
            self.last_run = time.time()


def main():
    mode = os.getenv("SCRAPER_MODE", "incremental")
    db = SessionLocal()
    repository = ScraperRepository(db)
    
    runners = []

    # --- Fuente Prefectura Naval ---
    prefectura_syncer = PrefecturaStationSyncer()
    if mode == "backfill":
        backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
        prefectura_strategy = PrefecturaBackFillStrategy(backfill_days)
    else:
        prefectura_strategy = PrefecturaIncrementalStrategy()

    context_prefectura = ScraperContext(prefectura_strategy, prefectura_syncer, repository)
    runners.append(SourceRunner(
        name="Prefectura",
        context=context_prefectura,
        interval=config.PREFECTURA_INTERVAL,
    ))

    # --- Fuente INA ---
    if config.INA_ENABLED:
        logger.info("=== INA source enabled ===")
        if mode == "backfill":
            backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
            ina_strategy = INABackFillStrategy(backfill_days)
        else:
            ina_strategy = INAIncrementalStrategy()

        context_ina = ScraperContext(ina_strategy, NoOpStationSyncer(), repository)
        runners.append(SourceRunner(
            name="INA",
            context=context_ina,
            interval=config.INA_INTERVAL,
        ))

    # --- Fuente CARU ---
    from scraper.caru.strategy import CARUIncrementalStrategy, CARUBackFillStrategy
    
    if config.CARU_ENABLED:
        logger.info("=== CARU source enabled ===")
        if mode == "backfill":
            backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
            caru_strategy = CARUBackFillStrategy(backfill_days)
        else:
            caru_strategy = CARUIncrementalStrategy()

        context_caru = ScraperContext(caru_strategy, NoOpStationSyncer(), repository)
        runners.append(SourceRunner(
            name="CARU",
            context=context_caru,
            interval=config.CARU_INTERVAL,
        ))

    # --- Bucle Principal (Scheduler) ---
    if mode == "backfill":
        logger.info(f"Running ONE-SHOT backfill mode for {os.getenv('BACKFILL_DAYS', '7')} days")
        for runner in runners:
            runner.run()
        logger.info("Backfill completed. Exiting.")
        return

    logger.info(f"Starting scraper scheduler. Tick interval: {config.SCRAPER_TICK}s")
    while True:
        for runner in runners:
            if runner.is_due():
                runner.run()
        
        time.sleep(config.SCRAPER_TICK)


if __name__ == "__main__":
    main()

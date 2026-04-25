from scraper.prefectura.strategy import PrefecturaIncrementalStrategy, PrefecturaBackFillStrategy
from scraper.ina.strategy import INAIncrementalStrategy, INABackFillStrategy
from scraper.prefectura.syncer import PrefecturaStationSyncer
from scraper.repository import ScraperRepository
from scraper.context import ScraperContext
from common.database import SessionLocal
import scraper.config as config
import os
import time
import logging
from common.database import engine
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


def main():
    mode = os.getenv("SCRAPER_MODE", "incremental")
    db = SessionLocal()
    repository = ScraperRepository(db)
    prefectura_syncer = PrefecturaStationSyncer()

    # --- Fuente Prefectura Naval ---
    if mode == "backfill":
        backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
        prefectura_strategy = PrefecturaBackFillStrategy(backfill_days)
    else:
        prefectura_strategy = PrefecturaIncrementalStrategy()

    context_prefectura = ScraperContext(prefectura_strategy, prefectura_syncer, repository)
    context_prefectura.execute()

    # --- Fuente INA ---
    if config.INA_ENABLED:
        logger.info("=== INA source enabled ===")
        if mode == "backfill":
            backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
            ina_strategy = INABackFillStrategy(backfill_days)
        else:
            ina_strategy = INAIncrementalStrategy()

        context_ina = ScraperContext(ina_strategy, NoOpStationSyncer(), repository)
        context_ina.execute()

    logger.info(
        f"Waiting {config.SCRAPER_INTERVAL} seconds "
        f"until the next execution..."
    )
    time.sleep(config.SCRAPER_INTERVAL)


if __name__ == "__main__":
    main()

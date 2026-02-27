from strategies import IncrementalStrategy, BackFillStrategy
from port_syncer import PortSyncer
from repository import ScraperRepository
from context import ScraperContext
from common.database import SessionLocal
import config
import os
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    mode = os.getenv("SCRAPER_MODE", "incremental")
    db = SessionLocal()
    repository = ScraperRepository(db)
    port_syncer = PortSyncer()

    if mode == "backfill":
        backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
        strategy = BackFillStrategy(backfill_days)
    else:
        strategy = IncrementalStrategy()

    context = ScraperContext(strategy, port_syncer, repository)
    context.execute()

    logger.info(
        f"Waiting {config.SCRAPER_INTERVAL} seconds "
        f"until the next execution..."
    )
    time.sleep(config.SCRAPER_INTERVAL)


if __name__ == "__main__":
    main()

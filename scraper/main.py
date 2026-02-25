from strategies import IncrementalStrategy, BackFillStrategy
from port_syncer import PortSyncer
from repository import ScraperRepository
from context import ScraperContext
from common.database import SessionLocal
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


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


if __name__ == "__main__":
    main()

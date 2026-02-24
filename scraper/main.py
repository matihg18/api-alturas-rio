from client import ScraperClient
from parser import IncrementalParser, BackFillParser
from strategies import IncrementalStrategy, BackFillStrategy
from repository import ScraperRepository
from context import ScraperContext
from common.database import SessionLocal
import os


def main():
    mode = os.getenv("SCRAPER_MODE", "incremental")
    db = SessionLocal()
    repository = ScraperRepository(db)

    if mode == "backfill":
        strategy = BackFillStrategy(
            os.getenv("START_DATE"),
            os.getenv("END_DATE")
        )
    else:
        strategy = IncrementalStrategy()
        context = ScraperContext(strategy, repository)
        context.execute()


if __name__ == "__main__":
    main()

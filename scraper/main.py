import os
import time
import logging
from dataclasses import dataclass, field
from typing import Callable

from scraper.prefectura.strategy import PrefecturaIncrementalStrategy, PrefecturaBackFillStrategy
from scraper.ina.strategy import INAIncrementalStrategy, INABackFillStrategy
from scraper.caru.strategy import CARUIncrementalStrategy, CARUBackFillStrategy
from scraper.municipalidadgchu.strategy import (
    MunicipalidadGchuIncrementalStrategy,
    MunicipalidadGchuBackFillStrategy,
)
from scraper.sgb.strategy import SGBIncrementalStrategy, SGBBackFillStrategy
from scraper.prefectura.syncer import PrefecturaStationSyncer
from scraper.repository import ScraperRepository
from scraper.context import ScraperContext
import scraper.config as config
from common.database import SessionLocal, engine
from common.models import Base
from scraper.base import BaseStationSyncer, ScraperStrategy

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


class NoOpStationSyncer(BaseStationSyncer):
    """Syncer vacío para fuentes que descubren sus estaciones durante el scraping."""

    def sync(self):
        return []


@dataclass
class SourceDefinition:
    """Declara una fuente de datos y todos sus parámetros de ejecución.

    Para agregar una nueva fuente, alcanza con añadir una instancia de esta
    clase al registro SOURCES — el orquestador no necesita modificarse.
    """
    name: str
    enabled: bool
    interval: int
    make_incremental: Callable[[], ScraperStrategy]
    make_backfill: Callable[[int], ScraperStrategy]
    make_syncer: Callable[[], BaseStationSyncer]
    # Ríos de interés para esta fuente. Lista vacía = sin filtro (acepta todo).
    allowed_rivers: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Registro de fuentes
# Para añadir una fuente nueva: agregar una SourceDefinition acá.
# ---------------------------------------------------------------------------
SOURCES: list[SourceDefinition] = [
    SourceDefinition(
        name="Prefectura",
        enabled=config.PREFECTURA_ENABLED,
        interval=config.PREFECTURA_INTERVAL,
        make_incremental=PrefecturaIncrementalStrategy,
        make_backfill=lambda days: PrefecturaBackFillStrategy(days, allowed_rivers=config.ALLOWED_RIVERS),
        make_syncer=PrefecturaStationSyncer,
        allowed_rivers=config.ALLOWED_RIVERS,
    ),
    SourceDefinition(
        name="INA",
        enabled=config.INA_ENABLED,
        interval=config.INA_INTERVAL,
        make_incremental=lambda: INAIncrementalStrategy(allowed_rivers=config.ALLOWED_RIVERS),
        make_backfill=lambda days: INABackFillStrategy(days, allowed_rivers=config.ALLOWED_RIVERS),
        make_syncer=NoOpStationSyncer,
        allowed_rivers=config.ALLOWED_RIVERS,
    ),
    SourceDefinition(
        name="CARU",
        enabled=config.CARU_ENABLED,
        interval=config.CARU_INTERVAL,
        make_incremental=CARUIncrementalStrategy,
        make_backfill=CARUBackFillStrategy,
        make_syncer=NoOpStationSyncer,
        # CARU solo reporta estaciones del río Uruguay — no necesita filtro global.
        allowed_rivers=[],
    ),
    SourceDefinition(
        name="Municipalidad Gualeguaychú",
        enabled=config.MUNICIPALIDAD_GCHU_ENABLED,
        interval=config.MUNICIPALIDAD_GCHU_INTERVAL,
        make_incremental=MunicipalidadGchuIncrementalStrategy,
        make_backfill=MunicipalidadGchuBackFillStrategy,
        make_syncer=NoOpStationSyncer,
        # Solo reporta el río Gualeguaychú — filtro explícito para documentar la intención.
        allowed_rivers=["GUALEGUAYCHU"],
    ),
    SourceDefinition(
        name="SGB",
        enabled=config.SGB_ENABLED,
        interval=config.SGB_INTERVAL,
        make_incremental=SGBIncrementalStrategy,
        make_backfill=lambda days: SGBBackFillStrategy(days),
        make_syncer=NoOpStationSyncer,
        # SGB cubre la cuenca del Uruguay (Brasil): el río de cada estación
        # se asigna dinámicamente por el strategy — sin filtro global.
        allowed_rivers=[],
    ),
]


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


def build_runners(mode: str, backfill_days: int, repository: ScraperRepository) -> list[SourceRunner]:
    """Construye la lista de runners a partir del registro de fuentes."""
    runners = []
    for source in SOURCES:
        if not source.enabled:
            logger.info(f"Source '{source.name}' is disabled — skipping.")
            continue

        strategy = (
            source.make_backfill(backfill_days)
            if mode == "backfill"
            else source.make_incremental()
        )
        context = ScraperContext(
            strategy=strategy,
            station_syncer=source.make_syncer(),
            repository=repository,
            allowed_rivers=source.allowed_rivers,
        )
        runners.append(SourceRunner(
            name=source.name,
            context=context,
            interval=source.interval,
        ))
        logger.info(f"Source '{source.name}' registered (interval={source.interval}s).")

    return runners


def main():
    mode = os.getenv("SCRAPER_MODE", "incremental")
    backfill_days = int(os.getenv("BACKFILL_DAYS", "7"))
    db = SessionLocal()
    repository = ScraperRepository(db)
    runners = build_runners(mode, backfill_days, repository)

    # --- Modo backfill: ejecutar una sola vez y salir ---
    if mode == "backfill":
        logger.info(f"Running ONE-SHOT backfill mode for {backfill_days} days")
        for runner in runners:
            runner.run()
        logger.info("Backfill completed. Exiting.")
        return

    # --- Bucle Principal (Scheduler) ---
    logger.info(f"Starting scraper scheduler. Tick interval: {config.SCRAPER_TICK}s")
    while True:
        for runner in runners:
            if runner.is_due():
                runner.run()
        time.sleep(config.SCRAPER_TICK)


if __name__ == "__main__":
    main()

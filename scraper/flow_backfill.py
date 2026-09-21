import logging

from common.database import SessionLocal
from common.models import DischargeCurveParams, Measurement
from common.flow_service import FlowService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def main():
    db = SessionLocal()
    try:
        station_ids = [
            p.station_id
            for p in db.query(DischargeCurveParams).all()
        ]

        if not station_ids:
            logger.warning("No hay curvas de descarga configuradas en discharge_curve_params. Saliendo.")
            return

        logger.info(f"Backfill iniciado para {len(station_ids)} estaciones: {station_ids}")
        flow_service = FlowService(db)
        total_saved = 0
        total_skipped = 0

        for station_id in station_ids:
            offset = 0
            station_saved = 0
            station_skipped = 0
            logger.info(f"Procesando station_id={station_id}...")

            while True:
                batch = (
                    db.query(Measurement)
                    .filter(Measurement.station_id == station_id)
                    .order_by(Measurement.date_time)
                    .offset(offset)
                    .limit(BATCH_SIZE)
                    .all()
                )
                if not batch:
                    break

                for m in batch:
                    try:
                        if flow_service.compute_and_save(station_id, m.date_time, m.value):
                            db.commit()
                            station_saved += 1
                        else:
                            station_skipped += 1
                    except Exception as e:
                        db.rollback()
                        station_skipped += 1
                        logger.debug(f"  Omitido ({e.__class__.__name__}): station={station_id} dt={m.date_time}")

                offset += BATCH_SIZE
                logger.info(
                    f"  station_id={station_id} — {offset} registros procesados "
                    f"({station_saved} guardados, {station_skipped} omitidos hasta ahora)"
                )


            total_saved += station_saved
            total_skipped += station_skipped
            logger.info(
                f"station_id={station_id} completada: "
                f"{station_saved} guardados, {station_skipped} omitidos."
            )

        logger.info(
            f"Backfill completado. Total: {total_saved} guardados, {total_skipped} omitidos."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

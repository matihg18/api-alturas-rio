
from datetime import datetime
from typing import Protocol

from sqlalchemy.orm import Session
from sqlalchemy import select

from common.models import Measurement


class ImportStrategy(Protocol):
    def apply(
        self,
        parsed: list[tuple[datetime, float]],
        station_id: int,
        db: Session,
    ) -> tuple[int, int, int]:
        ...


class SkipStrategy:

    def apply(
        self,
        parsed: list[tuple[datetime, float]],
        station_id: int,
        db: Session,
    ) -> tuple[int, int, int]:
        existing_datetimes: set[datetime] = set(
            db.execute(
                select(Measurement.date_time).where(
                    Measurement.station_id == station_id
                )
            ).scalars().all()
        )

        new_measurements = [
            Measurement(station_id=station_id, date_time=dt, value=val)
            for dt, val in parsed
            if dt not in existing_datetimes
        ]

        inserted = len(new_measurements)
        skipped = len(parsed) - inserted
        updated = 0

        if new_measurements:
            db.add_all(new_measurements)
            db.commit()

        return inserted, skipped, updated


class OverrideStrategy:
    def apply(
        self,
        parsed: list[tuple[datetime, float]],
        station_id: int,
        db: Session,
    ) -> tuple[int, int, int]:
        existing: dict[datetime, Measurement] = {
            m.date_time: m
            for m in db.execute(
                select(Measurement).where(
                    Measurement.station_id == station_id
                )
            ).scalars().all()
        }

        inserted = 0
        updated = 0
        new_measurements: list[Measurement] = []

        for dt, val in parsed:
            if dt in existing:
                existing[dt].value = val
                updated += 1
            else:
                new_measurements.append(
                    Measurement(station_id=station_id, date_time=dt, value=val)
                )
                inserted += 1

        if new_measurements:
            db.add_all(new_measurements)

        db.commit()

        return inserted, 0, updated


def get_strategy(override: bool) -> ImportStrategy:
    return OverrideStrategy() if override else SkipStrategy()

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from common.models import Station, GaugeDatum, ReferenceZeroType


def get_offset(
    session: Session, station_id: int, datum_code: str
) -> Optional[float]:
    station = session.get(Station, station_id)
    if not station or station.gauge_point_id is None:
        return None

    stmt = (
        select(GaugeDatum)
        .join(ReferenceZeroType, GaugeDatum.datum_type_id == ReferenceZeroType.id)
        .where(
            GaugeDatum.gauge_point_id == station.gauge_point_id,
            ReferenceZeroType.code == datum_code.upper(),
        )
    )
    datum = session.execute(stmt).scalars().first()
    return datum.offset_local_to_datum if datum else None


def convert(value: float, offset: float) -> float:
    return round(value + offset, 2)

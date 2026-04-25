from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    composite
)
from .database import Base
import dataclasses


@dataclasses.dataclass
class Coordinates:
    latitud: float
    longitud: float


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    river: Mapped[str] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(50))
    latitud: Mapped[float] = mapped_column("latitud", Float)
    longitud: Mapped[float] = mapped_column("longitud", Float)
    coordinates: Mapped[Coordinates] = composite(
        Coordinates, latitud, longitud
    )
    alert_value: Mapped[Optional[float]] = mapped_column(Float)
    evacuation_value: Mapped[Optional[float]] = mapped_column(Float)
    measurements: Mapped[List["Measurement"]] = relationship(
        back_populates="station"
    )


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    station: Mapped["Station"] = relationship(back_populates="measurements")
    date_time: Mapped[datetime] = mapped_column(DateTime)
    value: Mapped[float] = mapped_column(Float)

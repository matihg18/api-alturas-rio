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


class Port (Base):
    __tablename__ = "port"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    river: Mapped[str] = mapped_column(String(50))
    latitud: Mapped[float] = mapped_column("latitud", Float)
    longitud: Mapped[float] = mapped_column("longitud", Float)
    coordinates: Mapped[Coordinates] = composite(
        Coordinates, latitud, longitud
    )
    alert_value: Mapped[Optional[float]] = mapped_column(Float)
    evacuation_value: Mapped[Optional[float]] = mapped_column(Float)
    measurements: Mapped[List["Measurement"]] = relationship(
        back_populates="port"
    )


class Measurement (Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    port_id: Mapped[int] = mapped_column(ForeignKey("port.id"))
    port: Mapped["Port"] = relationship(back_populates="measurements")
    date_time: Mapped[datetime] = mapped_column(DateTime)
    value: Mapped[float] = mapped_column(Float)

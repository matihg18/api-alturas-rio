from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, UniqueConstraint
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


class ReferenceZeroType(Base):
    __tablename__ = "reference_zero_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    datums: Mapped[List["GaugeDatum"]] = relationship(back_populates="datum_type")


class GaugePoint(Base):
    __tablename__ = "gauge_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    river: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    datums: Mapped[List["GaugeDatum"]] = relationship(back_populates="gauge_point")
    stations: Mapped[List["Station"]] = relationship(back_populates="gauge_point")


class GaugeDatum(Base):
    __tablename__ = "gauge_datums"
    __table_args__ = (UniqueConstraint("gauge_point_id", "datum_type_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    gauge_point_id: Mapped[int] = mapped_column(ForeignKey("gauge_points.id"))
    datum_type_id: Mapped[int] = mapped_column(ForeignKey("reference_zero_types.id"))
    offset_local_to_datum: Mapped[float] = mapped_column(Float)
    gauge_point: Mapped["GaugePoint"] = relationship(back_populates="datums")
    datum_type: Mapped["ReferenceZeroType"] = relationship(back_populates="datums")


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
    alert_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evacuation_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gauge_point_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gauge_points.id"), nullable=True
    )
    gauge_point: Mapped[Optional["GaugePoint"]] = relationship(back_populates="stations")
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

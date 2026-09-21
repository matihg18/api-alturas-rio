from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, UniqueConstraint, Integer, Boolean
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
    latitud: Optional[float]
    longitud: Optional[float]


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
    latitud: Mapped[Optional[float]] = mapped_column("latitud", Float, nullable=True)
    longitud: Mapped[Optional[float]] = mapped_column("longitud", Float, nullable=True)
    coordinates: Mapped[Coordinates] = composite(
        Coordinates, latitud, longitud
    )
    alert_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evacuation_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
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


class ScraperError(Base):
    __tablename__ = "scraper_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    station_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_type: Mapped[str] = mapped_column(String(50))
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class DischargeCurveParams(Base):
    __tablename__ = "discharge_curve_params"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id"), unique=True, index=True
    )
    a: Mapped[float] = mapped_column(Float, comment="Coeficiente multiplicador")
    b: Mapped[float] = mapped_column(Float, comment="Exponente potencial")
    h0: Mapped[float] = mapped_column(Float, comment="Nivel de caudal nulo [m]")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    station: Mapped["Station"] = relationship()


class FlowMeasurement(Base):
    __tablename__ = "flow_measurements"
    __table_args__ = (UniqueConstraint("station_id", "date_time"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), index=True)
    date_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    flow: Mapped[float] = mapped_column(Float, comment="Caudal estimado [m³/s]")
    station: Mapped["Station"] = relationship()

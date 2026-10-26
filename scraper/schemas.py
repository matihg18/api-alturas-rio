from pydantic import BaseModel, field_validator
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class RawStationData(BaseModel):
    name: str
    river: str
    source: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    alert_value: Optional[float] = None
    evacuation_value: Optional[float] = None

    @field_validator("alert_value", "evacuation_value", mode="before")
    @classmethod
    def parse_numeric_strings(cls, v: Any) -> Optional[float]:
        if v in ("-", "", "S/E", None):
            return None
        try:
            return float(str(v).replace(",", "."))
        except ValueError:
            logger.debug(f"No se pudo convertir a float: {v}")
            return None


class RawMeasurementData(BaseModel):
    station_name: str
    source: str
    date_time: datetime
    value: Optional[float] = None


@dataclass(frozen=True)
class PrecipitationPoint:
    station_id: int
    station_name: str
    latitud: float
    longitud: float


class RawPrecipitationData(BaseModel):
    station_id: int
    station_name: str
    date_time: datetime
    precipitation: float

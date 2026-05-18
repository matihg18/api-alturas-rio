from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class RawStationData(BaseModel):
    """Datos de una estación (sin mediciones)."""
    name: str = Field(alias="PUERTO")
    river: str = Field(alias="RIO")
    source: str = "prefectura"
    latitud: float = Field(alias="LATITUD")
    longitud: float = Field(alias="LONGITUD")
    alert_value: Optional[float] = Field(None, alias="ALERTA")
    evacuation_value: Optional[float] = Field(None, alias="EVACUACION")

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
    """Datos de una medición individual."""
    station_name: str
    date_time: datetime
    value: Optional[float] = None

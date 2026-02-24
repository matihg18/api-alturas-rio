import json
import re
import logging
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class RawPortData(BaseModel):
    name: str = Field(alias="PUERTO")
    river: str = Field(alias="RIO")
    latitud: float = Field(alias="LATITUD")
    longitud: float = Field(alias="LONGITUD")
    alert_value: Optional[float] = Field(None, alias="ALERTA")
    evacuacion_value: Optional[float] = Field(None, alias="EVACUACION")

    value: Optional[float] = Field(None, alias="ULTIMOREGISTRO")
    state: str = Field(alias="ESTADO")
    delta: Optional[float] = Field(None, alias="VARIACION")
    date_time_str: str = Field(alias="FECHAHORA")

    @field_validator(
        "value",
        "alert_value",
        "evacuacion_value",
        "delta",
        mode="before"
    )
    @classmethod
    def parse_numeric_strings(cls, v: Any) -> Optional[float]:
        if v in ("-", "", "S/E", None):
            return None
        try:
            return float(str(v).replace(",", "."))
        except ValueError:
            logger.debug(f"No se pudo convertir a float: {v}")
            return None

    @property
    def timestamp(self) -> datetime:
        meses = {
            'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
        }
        try:
            clean_str = self.date_time_str.upper()
            for esp, num in meses.items():
                if esp in clean_str:
                    clean_str = clean_str.replace(esp, num)

            return datetime.strptime(clean_str, "%d/%m/%y - %H%M")
        except Exception as e:
            logger.error(f"Error parseando fecha {self.date_time_str}: {e}")
            return datetime.now()


class IncrementalParser:
    def __init__(self):
        self.pattern = re.compile(r"var mapData = '(.*?)';", re.DOTALL)

    def parse(self, html_content: str) -> List[RawPortData]:
        match = self.pattern.search(html_content)
        if not match:
            logger.error("No se encontró mapData en el HTML")
            return []

        try:

            json_str = match.group(1).replace('\\/', '/')
            raw_list = json.loads(json_str)
            return [RawPortData(**item) for item in raw_list]
        except Exception as e:
            logger.error(f"Error en parseo: {e}")
            return []

class BackFillParser:
    def __init__(self):
        pass

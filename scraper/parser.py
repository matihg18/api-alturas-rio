import json
import re
import logging
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class RawPortData(BaseModel):
    # Mapeo para el modelo Port
    name: str = Field(alias="PUERTO")
    river: str = Field(alias="RIO")
    latitud: float = Field(alias="LATITUD")
    longitud: float = Field(alias="LONGITUD")
    alert_value: Optional[float] = Field(None, alias="ALERTA")
    evacuacion_value: Optional[float] = Field(None, alias="EVACUACION")

    # Mapeo para el modelo Measurement
    value: Optional[float] = Field(None, alias="ULTIMOREGISTRO")
    state: str = Field(alias="ESTADO")
    # Cambiamos a Optional para que acepte el None del validador
    delta: Optional[float] = Field(None, alias="VARIACION") 
    date_time_str: str = Field(alias="FECHAHORA")

    @field_validator("value", "alert_value", "evacuacion_value", "delta", mode="before")
    @classmethod
    def parse_numeric_strings(cls, v: Any) -> Optional[float]:
        """Convierte '-', 'S/E' o nulos en None, y strings numéricos en float"""
        # Prefectura usa '-' o 'S/E' para datos faltantes
        if v in ("-", "", "S/E", None):
            return None
        try:
            # Reemplazamos coma por punto y convertimos a float
            # Esto maneja negativos como '-3.77' correctamente
            return float(str(v).replace(",", "."))
        except ValueError:
            logger.debug(f"No se pudo convertir a float: {v}")
            return None

    @property
    def timestamp(self) -> datetime:
        """Parsea la fecha de Prefectura (ej: '14/FEB/26 - 1200')"""
        meses = {
            'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
        }
        try:
            # Limpiamos el string: de '14/FEB/26 - 1200' a '14/02/26-1200'
            clean_str = self.date_time_str.upper()
            for esp, num in meses.items():
                if esp in clean_str:
                    clean_str = clean_str.replace(esp, num)
            
            # Usamos el formato correcto para día/mes/año - hora
            return datetime.strptime(clean_str, "%d/%m/%y - %H%M")
        except Exception as e:
            logger.error(f"Error parseando fecha {self.date_time_str}: {e}")
            return datetime.now()

class PrefecturaParser:
    def __init__(self):
        self.pattern = re.compile(r"var mapData = '(.*?)';", re.DOTALL)

    def parse(self, html_content: str) -> List[RawPortData]:
        match = self.pattern.search(html_content)
        if not match:
            logger.error("No se encontró mapData en el HTML")
            return []

        try:
            # El replace es por si vienen barras de escape en el JS
            json_str = match.group(1).replace('\\/', '/')
            raw_list = json.loads(json_str)
            
            return [RawPortData(**item) for item in raw_list]
        except Exception as e:
            logger.error(f"Error en parseo: {e}")
            return []
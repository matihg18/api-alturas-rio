import logging
import re
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup
from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)

SOURCE = "caru"


class CARUParser:
    """Transforma HTML de CARU a modelos internos del scraper."""

    def parse_main_page(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extrae la lista de estaciones disponibles en la página principal.
        Retorna una lista de dicts con la info básica y el ID necesario
        para consultar el histórico.
        """
        stations_info = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Hay dos tablas en la página de CARU:
        # 1) Puertos
        # 2) Estaciones Automáticas
        
        tables = soup.find_all("table")
        for table in tables:
            tbody = table.find("tbody")
            if not tbody:
                continue
                
            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all(["th", "td"])
                if not cols:
                    continue
                    
                # El link al histórico suele estar en la primera columna (el nombre)
                a_tag = cols[0].find("a")
                if not a_tag or "href" not in a_tag.attrs:
                    continue
                    
                href = a_tag["href"]
                # Formato esperado: "/alturas/web/user/altura/ID"
                match = re.search(r"/altura/(\d+)", href)
                if not match:
                    continue
                    
                station_id = match.group(1)
                name = a_tag.get_text(strip=True)
                
                # Para CARU no tenemos latitud/longitud en la web
                stations_info.append({
                    "name": name,
                    "caru_id": station_id,
                    "river": "URUGUAY", # Todo en CARU es río Uruguay
                    "source": SOURCE,
                })
                
        return stations_info

    def stations_to_raw_data(self, stations_info: List[Dict[str, Any]]) -> List[RawStationData]:
        stations = []
        for info in stations_info:
            try:
                # latitud y longitud son None ya que ahora son Optional
                station = RawStationData.model_construct(
                    name=info["name"],
                    river=info["river"],
                    source=info["source"],
                    latitud=None,
                    longitud=None,
                    alert_value=None,
                    evacuation_value=None,
                )
                stations.append(station)
            except Exception as e:
                logger.warning(f"CARU: error creating RawStationData for '{info['name']}': {e}")
        return stations

    def parse_history(
        self, html_content: str, station_name: str, since_hours: int
    ) -> List[RawMeasurementData]:
        """
        Extrae las mediciones de la tabla histórica.
        Solo retorna mediciones más recientes que since_hours.
        """
        measurements: List[RawMeasurementData] = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        table = soup.find("table")
        if not table:
            logger.debug(f"CARU: no history table found for '{station_name}'")
            return []
            
        tbody = table.find("tbody")
        if not tbody:
            return []
            
        rows = tbody.find_all("tr")
        cutoff_time = datetime.now() - timedelta(hours=since_hours)
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
                
            fecha_hora_str = cols[0].get_text(strip=True)
            valor_str = cols[1].get_text(strip=True)
            
            try:
                # Formato: 18/05/2026 12:00
                dt = datetime.strptime(fecha_hora_str, "%d/%m/%Y %H:%M")
                
                if dt < cutoff_time:
                    continue # Salteamos si es más vieja que la ventana
                    
                if valor_str in ("-", "", "S/D", None):
                    continue
                    
                valor = float(valor_str.replace(",", "."))
                
                measurements.append(RawMeasurementData(
                    station_name=station_name,
                    source=SOURCE,
                    date_time=dt,
                    value=valor,
                ))
            except Exception as e:
                logger.debug(f"CARU: error parsing row for '{station_name}': {e}")
                
        return measurements

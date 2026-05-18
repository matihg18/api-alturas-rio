import logging
import re
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup
from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)

SOURCE = "caru"


class CARUParser:
    def parse_main_page(self, html_content: str) -> List[Dict[str, Any]]:
        stations_info = []
        soup = BeautifulSoup(html_content, "html.parser")
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
                    
                a_tag = cols[0].find("a")
                if not a_tag or "href" not in a_tag.attrs:
                    continue
                    
                href = a_tag["href"]
                match = re.search(r"/altura/(\d+)", href)
                if not match:
                    continue
                    
                station_id = match.group(1)
                name = a_tag.get_text(strip=True)
                
                stations_info.append({
                    "name": name,
                    "caru_id": station_id,
                    "river": "URUGUAY",
                    "source": SOURCE,
                })
                
        return stations_info

    def stations_to_raw_data(self, stations_info: List[Dict[str, Any]]) -> List[RawStationData]:
        stations = []
        for info in stations_info:
            try:
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
                dt = datetime.strptime(fecha_hora_str, "%d/%m/%Y %H:%M")
                
                if dt < cutoff_time:
                    continue
                    
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

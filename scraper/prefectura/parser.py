import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional, Any, Tuple
from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)


class PrefecturaIncrementalParser:
    """Parsea mapa.php para extraer estaciones y su última medición."""

    MESES = {
        'ENE': '01', 'JAN': '01',
        'FEB': '02',
        'MAR': '03',
        'ABR': '04', 'APR': '04',
        'MAY': '05',
        'JUN': '06',
        'JUL': '07',
        'AGO': '08', 'AUG': '08',
        'SEP': '09',
        'OCT': '10',
        'NOV': '11',
        'DIC': '12', 'DEC': '12'
    }

    def __init__(self):
        self.pattern = re.compile(r"var mapData = '(.*?)';", re.DOTALL)

    def parse(self, html_content: str) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        match = self.pattern.search(html_content)
        if not match:
            logger.error("No se encontró mapData en el HTML")
            return [], []

        try:
            json_str = match.group(1).replace('\\/', '/')
            raw_list = json.loads(json_str)

            stations = []
            measurements = []

            for item in raw_list:
                stations.append(RawStationData(**item))

                timestamp = self._parse_timestamp(item.get("FECHAHORA", ""))
                value = self._parse_float(item.get("ULTIMOREGISTRO"))

                if value is not None:
                    measurements.append(RawMeasurementData(
                        station_name=item["PUERTO"],
                        source="prefectura",
                        date_time=timestamp,
                        value=value,
                    ))

            return stations, measurements
        except Exception as e:
            logger.error(f"Error en parseo: {e}")
            return [], []

    def _parse_timestamp(self, date_str: str) -> datetime:
        try:
            clean_str = date_str.upper()
            for esp, num in self.MESES.items():
                if esp in clean_str:
                    clean_str = clean_str.replace(esp, num)
            return datetime.strptime(clean_str, "%d/%m/%y - %H%M")
        except Exception as e:
            logger.error(f"Error parseando fecha {date_str}: {e}")
            return datetime.now()

    @staticmethod
    def _parse_float(v: Any) -> Optional[float]:
        if v in ("-", "", "S/E", None):
            return None
        try:
            return float(str(v).replace(",", "."))
        except ValueError:
            return None


class PrefecturaBackFillParser:

    def __init__(self, base_domain: str):
        self.base_domain = base_domain

    def parse_port_urls(self, html_content: str) -> List[dict]:
        soup = BeautifulSoup(html_content, 'html.parser')
        ports_found = []

        table_body = soup.find('tbody')
        rows = table_body.find_all('tr') if table_body else soup.find_all('tr')

        for row in rows:
            th = row.find('th')
            if not th:
                continue

            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            port_info = {
                "name": th.get_text(strip=True),
                "river": cols[0].get_text(strip=True).upper(),
                "history_url": ""
            }

            link_tag = row.find('a', href=re.compile(r"page=historico"))
            if link_tag:
                href = link_tag['href'].replace('\n', '').strip()
                if href.startswith('/'):
                    href = self.base_domain + href
                port_info["history_url"] = href
                ports_found.append(port_info)

        logger.debug(f"Found {len(ports_found)} stations with history URLs")
        return ports_found

    def parse_history_table(
        self, html_content: str, station_name: str
    ) -> List[RawMeasurementData]:
        measurements = []
        pattern = re.compile(
            r"name:\s*'Registro',\s*data:\s*(\[\[.*?\]\])", re.DOTALL
        )
        match = pattern.search(html_content)

        if not match:
            return []

        try:
            raw_json = match.group(1)
            raw_json = raw_json.replace('Array', 'null')
            raw_points = json.loads(raw_json)

            for point in raw_points:
                ts_ms = point[0]
                val = point[1]
                if val is None:
                    continue
                measurements.append(RawMeasurementData(
                    station_name=station_name,
                    source="prefectura",
                    date_time=datetime.fromtimestamp(ts_ms / 1000.0),
                    value=float(val),
                ))

        except Exception as e:
            logger.error(f"Error parsing {station_name} JSON data: {e}")

        return measurements

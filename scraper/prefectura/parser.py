import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional, Any, Tuple
from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)

# Mapa de abreviaturas de meses (ES e EN) al formato numérico.
_MESES = {
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


def _parse_timestamp(date_str: str) -> datetime:
    """Convierte '14/FEB/26 - 1200' → datetime. Comparte lógica entre parsers."""
    try:
        clean_str = date_str.upper()
        for abbr, num in _MESES.items():
            if abbr in clean_str:
                clean_str = clean_str.replace(abbr, num)
        return datetime.strptime(clean_str, "%d/%m/%y - %H%M")
    except Exception as e:
        logger.error(f"Error parseando fecha '{date_str}': {e}")
        return datetime.now()


def _parse_float(v: Any) -> Optional[float]:
    """Convierte un valor de texto a float, devuelve None si es inválido."""
    if v in ("-", "", "S/E", None):
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


class PrefecturaIncrementalParser:
    """Parsea mapa.php para extraer estaciones y su última medición."""

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
                stations.append(RawStationData(
                    name=item["PUERTO"],
                    river=item["RIO"],
                    source="prefectura",
                    latitud=float(item["LATITUD"]) if item.get("LATITUD") is not None else None,
                    longitud=float(item["LONGITUD"]) if item.get("LONGITUD") is not None else None,
                    alert_value=item.get("ALERTA"),
                    evacuation_value=item.get("EVACUACION"),
                ))

                timestamp = _parse_timestamp(item.get("FECHAHORA", ""))
                value = _parse_float(item.get("ULTIMOREGISTRO"))

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

    def parse_recent_measurements(self, html_content: str) -> List[RawMeasurementData]:
        """Extrae el Último Registro y Registro Anterior de la tabla principal.

        La página de histórico tiene un lag: los datos más recientes solo aparecen
        en la tabla principal antes de que Prefectura actualice el histórico.
        Capturar estos dos puntos evita el bache de hasta 12h en el dashboard.
        El repositorio deduplica por (station_id, date_time), así que cuando el
        histórico se actualice y el incremental los vuelva a traer, no se duplican.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        measurements = []

        table_body = soup.find('tbody')
        rows = table_body.find_all('tr') if table_body else soup.find_all('tr')

        for row in rows:
            th = row.find('th')
            if not th:
                continue

            station_name = th.get_text(strip=True)

            def _get_td_text(label: str) -> Optional[str]:
                td = row.find('td', attrs={'data-label': label})
                return td.get_text(strip=True) if td else None

            # ── Último Registro ───────────────────────────────────────────
            value = _parse_float(_get_td_text('Ultimo Registro:'))
            fecha_td = row.find('td', attrs={'data-label': 'Fecha Hora:'})
            if fecha_td:
                b_tag = fecha_td.find('b')
                fecha_str = b_tag.get_text(strip=True) if b_tag else fecha_td.get_text(strip=True)
                if value is not None:
                    measurements.append(RawMeasurementData(
                        station_name=station_name,
                        source="prefectura",
                        date_time=_parse_timestamp(fecha_str),
                        value=value,
                    ))

            # ── Registro Anterior ─────────────────────────────────────────
            prev_value = _parse_float(_get_td_text('Registro Anterior:'))
            prev_fecha_str = _get_td_text('Fecha Anterior:')
            if prev_value is not None and prev_fecha_str:
                measurements.append(RawMeasurementData(
                    station_name=station_name,
                    source="prefectura",
                    date_time=_parse_timestamp(prev_fecha_str),
                    value=prev_value,
                ))

        logger.debug(f"parse_recent_measurements: {len(measurements)} measurements extracted")
        return measurements

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

import io
import re
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from bs4 import BeautifulSoup

from scraper.schemas import RawStationData, RawMeasurementData
from scraper.utils import normalize_river

logger = logging.getLogger(__name__)

SOURCE = "sgb"
RIVER_FALLBACK = "URUGUAY"

_STATION_RE = re.compile(
    r'pm=(\d+)&(?:amp;)?s=(\d+)&(?:amp;)?sr=(\d+)'
    r'.+?'
    r'L\.circleMarker\(\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]'
    r'.+?'
    r'\.bindTooltip\("([^"]+)"',
    re.DOTALL,
)

_RIVER_RE = re.compile(
    r'[Nn][\u00ed]vel\s+do\s+rio\s+([A-Za-z\u00C0-\u024F\s]+?)(?:\s+e\s+|\s*<|\s*\n)',
)


class SGBParser:

    def parse_stations_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Extrae la lista de estaciones del JS embebido en la página del mapa.

        Devuelve lista de dicts con: pm, s, sr, name, lat, lon.
        """
        stations = []
        for m in _STATION_RE.finditer(html):
            pm, s, sr, lat, lon, tooltip = m.groups()

            stations.append({
                "pm": pm,
                "s": s,
                "sr": sr,
                "name": tooltip.strip(),
                "lat": float(lat),
                "lon": float(lon),
                "river": RIVER_FALLBACK,
            })
        logger.info(f"SGB: found {len(stations)} stations in map page")
        return stations

    def parse_river_from_report(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            m = _RIVER_RE.search(text)
            if m:
                raw = m.group(1).strip()
                return normalize_river(raw)
        logger.debug("SGB: river name not found in report page, using fallback")
        return RIVER_FALLBACK

    def parse_csv(
        self,
        csv_text: str,
        station_name: str,
        river: str,
        since_hours: int,
    ) -> List[RawMeasurementData]:
        measurements: List[RawMeasurementData] = []
        cutoff = datetime.now() - timedelta(hours=since_hours)

        reader = csv.DictReader(
            io.StringIO(csv_text),
            delimiter=";",
        )
        for row in reader:
            fecha_str = (row.get("data_hora_medicao") or "").strip()
            valor_str = (row.get("indice") or "").strip()
            if not fecha_str or not valor_str:
                continue
            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                if dt < cutoff:
                    continue
                value_m = float(valor_str) / 100.0
                measurements.append(
                    RawMeasurementData(
                        station_name=station_name,
                        source=SOURCE,
                        date_time=dt,
                        value=value_m,
                    )
                )
            except (ValueError, TypeError) as e:
                logger.debug(f"SGB: error parsing CSV row for '{station_name}': {e}")

        return measurements

    def station_to_raw_data(self, info: Dict[str, Any]) -> RawStationData:
        return RawStationData.model_construct(
            name=info["name"],
            river=info["river"],
            source=SOURCE,
            latitud=info.get("lat"),
            longitud=info.get("lon"),
            alert_value=None,
            evacuation_value=None,
        )

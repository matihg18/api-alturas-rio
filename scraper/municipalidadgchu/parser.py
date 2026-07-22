import json
import re
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)

SOURCE = "municipalidad_gchu"
STATION_NAME = "Puerto Local - Gualeguaychú"
RIVER = "GUALEGUAYCHU"


class MunicipalidadGchuParser:

    _CHART_PATTERN = re.compile(
        r"var\s+lineChartData\s*=\s*(\{.*?\});", re.DOTALL
    )
    _UPDATE_HOUR_PATTERN = re.compile(r"actualizaci[oó]n\s+(\d{1,2})hs", re.IGNORECASE)

    @staticmethod
    def _build_station() -> RawStationData:
        return RawStationData.model_construct(
            name=STATION_NAME,
            river=RIVER,
            source=SOURCE,
            latitud=None,
            longitud=None,
            alert_value=None,
            evacuation_value=None,
        )

    @staticmethod
    def _parse_float(value) -> Optional[float]:
        try:
            return float(str(value).replace(",", "."))
        except (ValueError, TypeError):
            return None

    def parse_current(
        self, html_content: str
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        """Extrae el valor actual de la altura y construye una medición."""
        soup = BeautifulSoup(html_content, "html.parser")

        value = self._extract_current_value(soup)
        if value is None:
            logger.warning("MUNICIPALIDAD GCHU: current height value not found in HTML")
            return [], []

        timestamp = self._extract_timestamp(soup)
        station = self._build_station()
        measurement = RawMeasurementData(
            station_name=STATION_NAME,
            source=SOURCE,
            date_time=timestamp,
            value=value,
        )
        logger.info(
            f"MUNICIPALIDAD GCHU: current value = {value} m (timestamp {timestamp.strftime('%Y-%m-%d %H:%M')})"
        )
        return [station], [measurement]

    def _extract_current_value(self, soup: BeautifulSoup) -> Optional[float]:
        h4_tags = soup.find_all("h4")
        for h4 in h4_tags:
            if "ALTURA DEL RIO" in h4.get_text(strip=True).upper():
                h3 = h4.find_next_sibling("h3")
                if h3:
                    span = h3.find("span")
                    if span:
                        return self._parse_float(span.get_text(strip=True))
        for h3 in soup.find_all("h3"):
            if "puerto local" in h3.get_text(strip=True).lower():
                span = h3.find("span")
                if span:
                    return self._parse_float(span.get_text(strip=True))
        return None

    def _extract_timestamp(self, soup: BeautifulSoup) -> datetime:
        now = datetime.now()
        p_tags = soup.find_all("p")
        for p in p_tags:
            text = p.get_text(strip=True)
            match = self._UPDATE_HOUR_PATTERN.search(text)
            if match:
                hour = int(match.group(1))
                candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if candidate > now:
                    candidate -= timedelta(days=1)
                return candidate
        return now.replace(minute=0, second=0, microsecond=0)

    def parse_history(
        self, html_content: str, since_hours: int
    ) -> Tuple[List[RawStationData], List[RawMeasurementData]]:
        measurements = self._parse_chart_data(html_content, since_hours)
        if not measurements:
            logger.warning("MUNICIPALIDAD GCHU: no historical data found in lineChartData")
            return [], []
        station = self._build_station()
        logger.info(f"MUNICIPALIDAD GCHU: {len(measurements)} valid observations found")
        return [station], measurements

    def _parse_chart_data(
        self, html_content: str, since_hours: int
    ) -> List[RawMeasurementData]:
        """
        Parsea el objeto JS lineChartData.  El objeto usa claves sin comillas
        (JS válido, JSON inválido), por lo que se normaliza con regex primero.
        """
        match = self._CHART_PATTERN.search(html_content)
        if not match:
            logger.debug("MUNICIPALIDAD GCHU: lineChartData variable not found in page")
            return []

        raw_js = match.group(1)
        # 1. Desescapar \/ -> / para que los valores de string sean válidos
        raw_js = raw_js.replace("\\/", "/")
        # 2. Convertir claves sin comillas a JSON válido: labels: -> "labels":
        normalized = re.sub(
            r'(?m)^\s*(\w+)\s*:',
            lambda mo: f'"{mo.group(1)}":',
            raw_js,
        )

        try:
            chart = json.loads(normalized)
        except json.JSONDecodeError as e:
            logger.error(f"MUNICIPALIDAD GCHU: failed to parse lineChartData JSON: {e}")
            return []

        labels: List[str] = chart.get("labels", [])
        datasets: List[dict] = chart.get("datasets", [])
        if not datasets:
            return []

        data_values = datasets[0].get("data", [])
        if len(labels) != len(data_values):
            logger.warning(
                f"MUNICIPALIDAD GCHU: labels count ({len(labels)}) "
                f"!= data count ({len(data_values)})"
            )

        cutoff = datetime.now() - timedelta(hours=since_hours)
        current_year = datetime.now().year
        measurements: List[RawMeasurementData] = []

        for label, raw_value in zip(labels, data_values):
            if raw_value is None:
                continue
            value = self._parse_float(raw_value)
            if value is None:
                continue
            dt = self._parse_chart_label(label, current_year)
            if dt is None or dt < cutoff:
                continue
            measurements.append(RawMeasurementData(
                station_name=STATION_NAME,
                source=SOURCE,
                date_time=dt,
                value=value,
            ))

        return measurements

    @staticmethod
    def _parse_chart_label(label: str, year: int) -> Optional[datetime]:
        label_clean = label.replace(" hs", "").strip()
        try:
            dt = datetime.strptime(f"{label_clean}/{year}", "%d/%m %H:%M/%Y")
            if dt.month == 12 and datetime.now().month == 1:
                dt = dt.replace(year=year - 1)
            return dt
        except ValueError:
            logger.debug(f"MUNICIPALIDAD GCHU: could not parse chart label '{label}'")
            return None

import logging
from datetime import datetime, timezone
from typing import List
from scraper.schemas import RawStationData, RawMeasurementData

logger = logging.getLogger(__name__)

SOURCE = "ina"


class INAParser:
    """Transforma respuestas JSON de la API INA a modelos internos del scraper."""

    def parse_series(self, series_list: List[dict]) -> List[RawStationData]:
        """
        Convierte una lista de series INA (ya filtradas) en RawStationData.
        Cada serie contiene la info de la estación embebida en 'estacion'.
        """
        stations: List[RawStationData] = []
        seen = set()

        for serie in series_list:
            estacion = serie.get("estacion")
            if not estacion:
                continue

            nombre = estacion.get("nombre", "").strip()
            if not nombre or nombre in seen:
                continue
            seen.add(nombre)

            geom = estacion.get("geom") or {}
            coords = geom.get("coordinates", [None, None])
            longitud = coords[0]
            latitud = coords[1]

            if latitud is None or longitud is None:
                logger.debug(f"INA: skipping station '{nombre}' — missing coordinates")
                continue

            try:
                station = RawStationData.model_construct(
                    name=nombre,
                    river=(estacion.get("rio") or "").upper(),
                    source=SOURCE,
                    latitud=float(latitud),
                    longitud=float(longitud),
                    alert_value=estacion.get("nivel_alerta"),
                    evacuation_value=estacion.get("nivel_evacuacion"),
                )
                stations.append(station)
            except Exception as e:
                logger.warning(f"INA: error parsing station '{nombre}': {e}")

        logger.info(f"INA: {len(stations)} unique stations parsed")
        return stations

    def parse_observations(
        self,
        obs_list: List[dict],
        station_name: str,
    ) -> List[RawMeasurementData]:
        """
        Convierte observaciones crudas de la API INA a RawMeasurementData.
        """
        measurements: List[RawMeasurementData] = []

        for obs in obs_list:
            valor = obs.get("valor")
            if valor is None:
                continue

            timestart_raw = obs.get("timestart")
            if not timestart_raw:
                continue

            try:
                # La API devuelve ISO 8601 con 'Z' o offset
                dt = datetime.fromisoformat(
                    timestart_raw.replace("Z", "+00:00")
                ).astimezone().replace(tzinfo=None)

                measurements.append(RawMeasurementData(
                    station_name=station_name,
                    source="ina",
                    date_time=dt,
                    value=float(valor),
                ))
            except Exception as e:
                logger.debug(f"INA: error parsing observation for '{station_name}': {e}")

        return measurements

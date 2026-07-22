import re
import unicodedata


def normalize_river(s: str) -> str:
    """Normaliza a mayúsculas sin diacríticos: 'Paraná' → 'PARANA'."""
    if not s:
        return ""
    return unicodedata.normalize("NFD", s.upper()).encode("ascii", "ignore").decode()


def is_river_allowed(station_river: str, allowed_rivers: list[str]) -> bool:
    """
    Determina si el río de una estación coincide con la lista de ríos permitidos.
    Soporta:
    - Coincidencia exacta (ej: 'URUGUAY' == 'Uruguay')
    - Coincidencia de palabra completa (ej: 'PARANA' en 'Delta del Paraná')
    - Variaciones/secciones concatenadas de fuentes como INA (ej: 'PARANAMED', 'PARANAINF', 'PARANADELASPALMAS', 'PARANAGUAZU', etc.)
    """
    if not allowed_rivers:
        return True

    norm_station = normalize_river(station_river)
    if not norm_station:
        return False

    for allowed in allowed_rivers:
        norm_allowed = normalize_river(allowed)
        if not norm_allowed:
            continue

        # 1. Coincidencia exacta
        if norm_station == norm_allowed:
            return True

        # 2. Coincidencia como palabra completa (ej: 'DELTA DEL PARANA', 'URUGUAY - EL SOBERBIO')
        if re.search(r'\b' + re.escape(norm_allowed) + r'\b', norm_station):
            return True

        # 3. Sufijos/secciones de códigos de fuentes como INA (PARANAMED, PARANAINF, PARANASUP, etc.)
        if norm_station.startswith(norm_allowed):
            suffix = norm_station[len(norm_allowed):]
            if suffix in ('MED', 'INF', 'SUP', 'DELASPALMAS', 'GUAZU', 'IBICUY', 'MINI', 'SANTAFE', 'BONAERENSE'):
                return True

    return False

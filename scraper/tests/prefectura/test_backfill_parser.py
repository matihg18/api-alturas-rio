from scraper.prefectura.parser import PrefecturaBackFillParser


BASE_DOMAIN = "https://contenidosweb.prefecturanaval.gob.ar"


def test_parse_port_urls_extracts_ports(html_pagina_principal):
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    ports = parser.parse_port_urls(html_pagina_principal)

    assert len(ports) == 2
    assert ports[0]["name"] == "COLON"
    assert ports[0]["river"] == "URUGUAY"
    assert ports[1]["name"] == "CONCORDIA"


def test_parse_port_urls_builds_absolute_urls(html_pagina_principal):
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    ports = parser.parse_port_urls(html_pagina_principal)

    assert ports[0]["history_url"].startswith("https://")
    assert "page=historico" in ports[0]["history_url"]
    assert "id=550" in ports[0]["history_url"]


def test_parse_port_urls_empty_html():
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    ports = parser.parse_port_urls("<html><body></body></html>")

    assert ports == []


def test_parse_recent_measurements_extracts_both_points(html_pagina_principal):
    """Debe extraer Último Registro y Registro Anterior por estación."""
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    measurements = parser.parse_recent_measurements(html_pagina_principal)

    # 2 estaciones × 2 puntos (último + anterior) = 4
    assert len(measurements) == 4
    names = [m.station_name for m in measurements]
    assert names.count("COLON") == 2
    assert names.count("CONCORDIA") == 2


def test_parse_recent_measurements_values(html_pagina_principal):
    """Verifica valores y timestamps correctos para COLON."""
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    measurements = parser.parse_recent_measurements(html_pagina_principal)

    colon_meds = [m for m in measurements if m.station_name == "COLON"]
    values = {m.value for m in colon_meds}
    assert 2.15 in values  # Último Registro
    assert 1.75 in values  # Registro Anterior

    # Último Registro: 14/FEB/26 - 1200
    ultimo = next(m for m in colon_meds if m.value == 2.15)
    assert ultimo.date_time.day == 14
    assert ultimo.date_time.month == 2
    assert ultimo.date_time.hour == 12

    # Registro Anterior: 13/FEB/26 - 1200
    anterior = next(m for m in colon_meds if m.value == 1.75)
    assert anterior.date_time.day == 13


def test_parse_recent_measurements_empty_html():
    """HTML sin tabla devuelve lista vacía."""
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    measurements = parser.parse_recent_measurements("<html><body></body></html>")
    assert measurements == []


def test_parse_history_table_extracts_measurements(html_historico_normal):
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    measurements = parser.parse_history_table(html_historico_normal, "COLON")

    assert len(measurements) == 3
    assert measurements[0].station_name == "COLON"
    assert measurements[0].value == 2.15
    assert measurements[1].value == 1.75
    assert measurements[2].value == 1.50


def test_parse_history_table_skips_array_values(html_historico_con_array):
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    measurements = parser.parse_history_table(html_historico_con_array, "TEST")

    assert len(measurements) == 2
    assert measurements[0].value == 2.15
    assert measurements[1].value == 1.50


def test_parse_history_table_no_data(html_historico_sin_datos):
    parser = PrefecturaBackFillParser(BASE_DOMAIN)
    measurements = parser.parse_history_table(html_historico_sin_datos, "TEST")

    assert measurements == []

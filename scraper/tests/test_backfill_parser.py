from parser import BackFillParser


BASE_DOMAIN = "https://contenidosweb.prefecturanaval.gob.ar"


def test_parse_port_urls_extracts_ports(html_pagina_principal):
    parser = BackFillParser(BASE_DOMAIN)
    ports = parser.parse_port_urls(html_pagina_principal)

    assert len(ports) == 2
    assert ports[0]["name"] == "COLON"
    assert ports[0]["river"] == "URUGUAY"
    assert ports[1]["name"] == "CONCORDIA"


def test_parse_port_urls_builds_absolute_urls(html_pagina_principal):
    parser = BackFillParser(BASE_DOMAIN)
    ports = parser.parse_port_urls(html_pagina_principal)

    assert ports[0]["history_url"].startswith("https://")
    assert "page=historico" in ports[0]["history_url"]
    assert "id=550" in ports[0]["history_url"]


def test_parse_port_urls_empty_html():
    parser = BackFillParser(BASE_DOMAIN)
    ports = parser.parse_port_urls("<html><body></body></html>")

    assert ports == []


def test_parse_history_table_extracts_measurements(html_historico_normal):
    parser = BackFillParser(BASE_DOMAIN)
    measurements = parser.parse_history_table(html_historico_normal, "COLON")

    assert len(measurements) == 3
    assert measurements[0].port_name == "COLON"
    assert measurements[0].value == 2.15
    assert measurements[1].value == 1.75
    assert measurements[2].value == 1.50


def test_parse_history_table_skips_array_values(html_historico_con_array):
    parser = BackFillParser(BASE_DOMAIN)
    measurements = parser.parse_history_table(html_historico_con_array, "TEST")

    assert len(measurements) == 2
    assert measurements[0].value == 2.15
    assert measurements[1].value == 1.50


def test_parse_history_table_no_data(html_historico_sin_datos):
    parser = BackFillParser(BASE_DOMAIN)
    measurements = parser.parse_history_table(html_historico_sin_datos, "TEST")

    assert measurements == []

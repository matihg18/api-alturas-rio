from parser import IncrementalParser


def test_parser_extracts_ports_and_measurements(html_ejemplo_prefectura):
    parser = IncrementalParser()

    ports, measurements = parser.parse(html_ejemplo_prefectura)

    assert len(ports) == 2
    assert len(measurements) == 2

    puerto_colon = ports[0]
    assert puerto_colon.name == "COLON"
    assert puerto_colon.river == "URUGUAY"
    assert puerto_colon.latitud == -32.22

    medicion_colon = measurements[0]
    assert medicion_colon.port_name == "COLON"
    assert medicion_colon.value == 2.15


def test_parser_port_data_has_no_measurement_fields(html_ejemplo_prefectura):
    parser = IncrementalParser()
    ports, _ = parser.parse(html_ejemplo_prefectura)

    puerto = ports[0]
    assert hasattr(puerto, 'latitud')
    assert hasattr(puerto, 'longitud')
    assert not hasattr(puerto, 'value')
    assert not hasattr(puerto, 'state')


def test_parser_manage_invalid_data(html_datos_invalidos):
    parser = IncrementalParser()

    ports, measurements = parser.parse(html_datos_invalidos)

    assert ports[0].alert_value is None
    assert len(measurements) == 0


def test_timestamp_conversion(html_ejemplo_prefectura):
    parser = IncrementalParser()
    _, measurements = parser.parse(html_ejemplo_prefectura)

    ts = measurements[0].date_time
    assert ts.day == 14
    assert ts.month == 2
    assert ts.year == 2026

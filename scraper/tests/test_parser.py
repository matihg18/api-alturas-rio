from parser import IncrementalParser


def test_parser_extracts_data_correctly(html_ejemplo_prefectura):
    parser = IncrementalParser()

    resultados = parser.parse(html_ejemplo_prefectura)

    assert len(resultados) == 2
    puerto_colon = resultados[0]
    assert puerto_colon.name == "COLON"
    assert puerto_colon.river == "URUGUAY"
    assert puerto_colon.latitud == -32.22
    assert puerto_colon.value == 2.15


def test_parser_manage_invalidad_data(html_datos_invalidos):
    parser = IncrementalParser()

    resultados = parser.parse(html_datos_invalidos)

    assert resultados[0].alert_value is None


def test_timestamp_conversion(html_ejemplo_prefectura):
    parser = IncrementalParser()
    resultados = parser.parse(html_ejemplo_prefectura)

    ts = resultados[0].timestamp
    assert ts.day == 14
    assert ts.month == 2
    assert ts.year == 2026

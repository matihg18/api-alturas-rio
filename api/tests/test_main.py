def test_get_station_list_endpoint(client, seed_data):
    response = client.get("/stations")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3
    assert data["items"][0]["name"] == "testStation1"


def test_get_station_by_id_endpoint(client, seed_data):
    response = client.get("/stations/1")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "testStation1"
    assert data["gauge_point_id"] == 1

    response = client.get("/stations/4")
    assert response.status_code == 404


def test_get_measurements_by_station_id_endpoint(client, seed_data):
    response = client.get("/measurements/1")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert data["items"][0]["value"] == 4.7
    # Sin datum, el formato siempre incluye estos campos con valores por defecto
    assert data["datum_used"] == "LOCAL"
    assert data["conversion_available"] is False


def test_get_measurements_with_datum_conversion(client, seed_data):
    # station_1 tiene gauge_point con offset IGN = +1.0
    response = client.get("/measurements/1?datum=IGN")

    assert response.status_code == 200
    data = response.json()
    assert data["datum_used"] == "IGN"
    assert data["conversion_available"] is True
    # value debe ser el valor convertido (local + offset): 4.7 + 1.0 = 5.7
    assert data["items"][0]["value"] == 5.7
    assert data["items"][1]["value"] == 6.1


def test_get_measurements_datum_not_available(client, seed_data):
    # station_2 no tiene gauge_point → sin conversión disponible
    response = client.get("/measurements/2?datum=IGN")

    assert response.status_code == 200
    data = response.json()
    assert data["datum_used"] == "LOCAL"
    assert data["conversion_available"] is False
    # value debe ser el local original
    assert data["items"][0]["value"] == 4.1


def test_get_latest_measurement_by_station_id_endpoint(client, seed_data):
    response = client.get("/measurements/latest/1")

    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 5.1
    assert data["datum_used"] == "LOCAL"
    assert data["conversion_available"] is False

    response = client.get("/measurements/latest/4")
    assert response.status_code == 404

    response = client.get("/measurements/latest/3")
    assert response.status_code == 404


def test_get_latest_measurement_with_datum(client, seed_data):
    # station_1 con ?datum=IGN: 5.1 + 1.0 = 6.1
    response = client.get("/measurements/latest/1?datum=IGN")

    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 6.1
    assert data["datum_used"] == "IGN"
    assert data["conversion_available"] is True


def test_get_stations_with_active_alert_endpoint(client, seed_data):
    response = client.get("/alerts")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2


def test_get_stations_with_evacuation_alert_endpoint(client, seed_data):
    response = client.get("/alerts/evacuation")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["items"][0]["id"] == 2


def test_get_datum_types_endpoint(client, seed_data):
    response = client.get("/datums")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "IGN"


def test_get_gauge_point_for_station_endpoint(client, seed_data):
    # station_1 tiene gauge_point asignado
    response = client.get("/datums/station/1")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TestPoint"
    assert len(data["datums"]) == 1
    assert data["datums"][0]["offset_local_to_datum"] == 1.0
    assert data["datums"][0]["datum_type"]["code"] == "IGN"


def test_get_gauge_point_for_station_not_linked(client, seed_data):
    # station_2 no tiene gauge_point → 404
    response = client.get("/datums/station/2")
    assert response.status_code == 404


def test_get_gauge_point_for_station_not_found(client, seed_data):
    # station inexistente → 404
    response = client.get("/datums/station/99")
    assert response.status_code == 404

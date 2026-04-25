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

    response = client.get("/stations/4")
    assert response.status_code == 404


def test_get_measurements_by_station_id_endpoint(client, seed_data):
    response = client.get("/measurements/1")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert data["items"][0]["value"] == 4.7


def test_get_latest_measurement_by_station_id_endpoint(client, seed_data):
    response = client.get("/measurements/latest/1")

    assert response.status_code == 200
    data = response.json()
    assert data["value"] == 5.1

    response = client.get("/measurements/latest/4")
    assert response.status_code == 404

    response = client.get("/measurements/latest/3")
    assert response.status_code == 404


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

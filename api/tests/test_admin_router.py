# Tests de integración para el admin router (/admin/*)
# Usa los fixtures `client` y `seed_data` definidos en conftest.py.
# seed_data provee: ReferenceZeroType(id=1, code="IGN"), GaugePoint(id=1),
#   GaugeDatum(id=1, gp=1, dt=1, offset=1.0), Station(id=1..3).


# ─────────────────────────────────────────────────────────────────────────────
# Stations
# ─────────────────────────────────────────────────────────────────────────────

def test_admin_list_stations(client, seed_data):
    r = client.get("/admin/stations")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 3
    ids = [s["id"] for s in data]
    assert 1 in ids and 2 in ids and 3 in ids
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "gauge_point_id" in first


def test_admin_list_stations_includes_gauge_point(client, seed_data):
    """La estación 1 tiene gauge_point asignado; debe aparecer en la respuesta."""
    r = client.get("/admin/stations")
    assert r.status_code == 200
    station_1 = next(s for s in r.json() if s["id"] == 1)
    assert station_1["gauge_point_id"] == 1
    assert station_1["gauge_point"]["name"] == "TestPoint"


def test_admin_assign_gauge_point(client, seed_data):
    """Asignar gauge_point_id=1 a la estación 2 (que no tenía)."""
    r = client.put("/admin/stations/2/gauge-point", json={"gauge_point_id": 1})
    assert r.status_code == 200
    assert r.json()["gauge_point_id"] == 1


def test_admin_unassign_gauge_point(client, seed_data):
    """Pasar gauge_point_id=null desvincula el punto de aforo."""
    r = client.put("/admin/stations/1/gauge-point", json={"gauge_point_id": None})
    assert r.status_code == 200
    assert r.json()["gauge_point_id"] is None


def test_admin_assign_gauge_point_station_not_found(client, seed_data):
    r = client.put("/admin/stations/999/gauge-point", json={"gauge_point_id": 1})
    assert r.status_code == 404


def test_admin_assign_gauge_point_gp_not_found(client, seed_data):
    """El gauge_point_id que se quiere asignar no existe → 404."""
    r = client.put("/admin/stations/2/gauge-point", json={"gauge_point_id": 999})
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Gauge Points
# ─────────────────────────────────────────────────────────────────────────────

def test_admin_list_gauge_points(client, seed_data):
    r = client.get("/admin/gauge-points")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "TestPoint"
    assert data[0]["river"] == "testRiver"


def test_admin_create_gauge_point(client, seed_data):
    payload = {"name": "Concordia", "river": "Uruguay", "description": "Estación Concordia"}
    r = client.post("/admin/gauge-points", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Concordia"
    assert data["river"] == "Uruguay"
    assert data["id"] is not None


def test_admin_create_gauge_point_minimal(client, seed_data):
    """Solo el nombre es obligatorio; river y description son opcionales."""
    r = client.post("/admin/gauge-points", json={"name": "Solo nombre"})
    assert r.status_code == 201
    assert r.json()["name"] == "Solo nombre"
    assert r.json()["river"] is None


def test_admin_update_gauge_point(client, seed_data):
    r = client.put("/admin/gauge-points/1", json={"name": "TestPoint Actualizado"})
    assert r.status_code == 200
    assert r.json()["name"] == "TestPoint Actualizado"
    assert r.json()["river"] == "testRiver"


def test_admin_update_gauge_point_not_found(client, seed_data):
    r = client.put("/admin/gauge-points/999", json={"name": "No existe"})
    assert r.status_code == 404


def test_admin_delete_gauge_point(client, seed_data):
    # Creamos uno nuevo para no afectar el seed de otros tests
    r_create = client.post("/admin/gauge-points", json={"name": "Para eliminar"})
    new_id = r_create.json()["id"]

    r_delete = client.delete(f"/admin/gauge-points/{new_id}")
    assert r_delete.status_code == 204

    ids = [gp["id"] for gp in client.get("/admin/gauge-points").json()]
    assert new_id not in ids


def test_admin_delete_gauge_point_not_found(client, seed_data):
    r = client.delete("/admin/gauge-points/999")
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Datum Types
# ─────────────────────────────────────────────────────────────────────────────

def test_admin_list_datum_types(client, seed_data):
    r = client.get("/admin/datum-types")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["code"] == "IGN"


def test_admin_create_datum_type(client, seed_data):
    payload = {"code": "wgs84", "name": "WGS 84", "description": "Datum geodésico global"}
    r = client.post("/admin/datum-types", json=payload)
    assert r.status_code == 201
    data = r.json()
    # El código debe guardarse en mayúsculas
    assert data["code"] == "WGS84"
    assert data["name"] == "WGS 84"


def test_admin_create_datum_type_duplicate_code(client, seed_data):
    """Crear un datum type con código ya existente → 409 Conflict."""
    r = client.post("/admin/datum-types", json={"code": "IGN", "name": "Duplicado"})
    assert r.status_code == 409


def test_admin_update_datum_type(client, seed_data):
    r = client.put("/admin/datum-types/1", json={"name": "Cero IGN Actualizado"})
    assert r.status_code == 200
    assert r.json()["name"] == "Cero IGN Actualizado"
    # El código no cambia (es inmutable por diseño)
    assert r.json()["code"] == "IGN"


def test_admin_update_datum_type_not_found(client, seed_data):
    r = client.put("/admin/datum-types/999", json={"name": "No existe"})
    assert r.status_code == 404


def test_admin_delete_datum_type(client, seed_data):
    r_create = client.post("/admin/datum-types", json={"code": "TMP", "name": "Temporal"})
    new_id = r_create.json()["id"]

    r_delete = client.delete(f"/admin/datum-types/{new_id}")
    assert r_delete.status_code == 204

    ids = [dt["id"] for dt in client.get("/admin/datum-types").json()]
    assert new_id not in ids


def test_admin_delete_datum_type_not_found(client, seed_data):
    r = client.delete("/admin/datum-types/999")
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Offsets (GaugeDatum)
# ─────────────────────────────────────────────────────────────────────────────

def test_admin_list_offsets(client, seed_data):
    r = client.get("/admin/offsets")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["offset_local_to_datum"] == 1.0
    assert data[0]["gauge_point"]["name"] == "TestPoint"
    assert data[0]["datum_type"]["code"] == "IGN"


def test_admin_list_offsets_filter_by_gauge_point(client, seed_data):
    """Filtro por gauge_point_id=1 devuelve solo los de ese punto."""
    r = client.get("/admin/offsets?gauge_point_id=1")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # gauge_point_id inexistente devuelve lista vacía, no 404
    r2 = client.get("/admin/offsets?gauge_point_id=999")
    assert r2.status_code == 200
    assert r2.json() == []


def test_admin_create_offset(client, seed_data):
    # Necesitamos un segundo datum type para crear un offset nuevo
    r_dt = client.post("/admin/datum-types", json={"code": "WGS84", "name": "WGS 84"})
    dt_id = r_dt.json()["id"]

    payload = {
        "gauge_point_id": 1,
        "datum_type_id": dt_id,
        "offset_local_to_datum": 2.5,
    }
    r = client.post("/admin/offsets", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["offset_local_to_datum"] == 2.5
    assert data["gauge_point"]["id"] == 1
    assert data["datum_type"]["code"] == "WGS84"


def test_admin_create_offset_duplicate(client, seed_data):
    """Intentar crear un offset para la misma combinación gp+datum → 409."""
    payload = {
        "gauge_point_id": 1,
        "datum_type_id": 1,  # ya existe en seed_data
        "offset_local_to_datum": 9.9,
    }
    r = client.post("/admin/offsets", json=payload)
    assert r.status_code == 409


def test_admin_create_offset_gauge_point_not_found(client, seed_data):
    payload = {"gauge_point_id": 999, "datum_type_id": 1, "offset_local_to_datum": 1.0}
    r = client.post("/admin/offsets", json=payload)
    assert r.status_code == 404


def test_admin_create_offset_datum_type_not_found(client, seed_data):
    payload = {"gauge_point_id": 1, "datum_type_id": 999, "offset_local_to_datum": 1.0}
    r = client.post("/admin/offsets", json=payload)
    assert r.status_code == 404


def test_admin_update_offset(client, seed_data):
    r = client.put("/admin/offsets/1", json={"offset_local_to_datum": 3.75})
    assert r.status_code == 200
    assert r.json()["offset_local_to_datum"] == 3.75


def test_admin_update_offset_not_found(client, seed_data):
    r = client.put("/admin/offsets/999", json={"offset_local_to_datum": 1.0})
    assert r.status_code == 404


def test_admin_delete_offset(client, seed_data):
    # Crear recursos auxiliares para no tocar el seed
    dt_id = client.post(
        "/admin/datum-types", json={"code": "DEL", "name": "Para eliminar"}
    ).json()["id"]
    off_id = client.post("/admin/offsets", json={
        "gauge_point_id": 1,
        "datum_type_id": dt_id,
        "offset_local_to_datum": 0.0,
    }).json()["id"]

    r = client.delete(f"/admin/offsets/{off_id}")
    assert r.status_code == 204

    remaining_ids = [o["id"] for o in client.get("/admin/offsets").json()]
    assert off_id not in remaining_ids


def test_admin_delete_offset_not_found(client, seed_data):
    r = client.delete("/admin/offsets/999")
    assert r.status_code == 404


def test_export_csv_returns_csv_content_type(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2026-02-01&to_date=2026-02-28")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_export_csv_has_correct_header(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2026-02-01&to_date=2026-02-28")
    assert r.status_code == 200
    first_line = r.text.splitlines()[0]
    assert first_line == "date_time,value"


def test_export_csv_includes_measurements_in_range(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2026-02-21&to_date=2026-02-22")
    assert r.status_code == 200
    lines = [l for l in r.text.splitlines() if l and not l.startswith("date_time")]
    assert len(lines) == 2
    values = [float(l.split(",")[1]) for l in lines]
    assert 4.7 in values
    assert 5.1 in values


def test_export_csv_excludes_measurements_outside_range(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2026-02-21&to_date=2026-02-21")
    assert r.status_code == 200
    lines = [l for l in r.text.splitlines() if l and not l.startswith("date_time")]
    assert len(lines) == 1
    assert float(lines[0].split(",")[1]) == 4.7


def test_export_csv_empty_range_returns_only_header(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2020-01-01&to_date=2020-01-31")
    assert r.status_code == 200
    lines = [l for l in r.text.splitlines() if l]
    assert lines == ["date_time,value"]


def test_export_csv_station_not_found(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=999&from_date=2026-01-01&to_date=2026-01-31")
    assert r.status_code == 404


def test_export_csv_filename_contains_station_name_and_id(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2026-02-01&to_date=2026-02-28")
    assert r.status_code == 200
    disposition = r.headers.get("content-disposition", "")
    assert "testStation1" in disposition
    assert "_1_" in disposition


def test_export_csv_from_date_after_to_date_returns_error(client, seed_data):
    r = client.get("/admin/measurements/export?station_id=1&from_date=2026-03-01&to_date=2026-02-01")
    assert r.status_code == 422


def _csv_file(content: str):
    return {"file": ("mediciones.csv", content.encode(), "text/csv")}


def test_import_csv_inserts_new_measurements(client, seed_data):
    csv_content = "date_time,value\n2026-01-10T00:00:00,3.50\n2026-01-10T06:00:00,3.75\n"
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert data["inserted"] == 2
    assert data["skipped"] == 0


def test_import_csv_skips_existing_measurements(client, seed_data):
    csv_content = (
        "date_time,value\n"
        "2026-02-21T00:00:00,99.99\n"
        "2026-02-22T00:00:00,99.99\n"
        "2026-01-05T00:00:00,2.80\n"
    )
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["inserted"] == 1
    assert data["skipped"] == 2


def test_import_csv_existing_values_not_overwritten(client, seed_data, db_session):
    from sqlalchemy import select
    from common.models import Measurement
    from datetime import datetime

    csv_content = "date_time,value\n2026-02-21T00:00:00,99.99\n"
    client.post("/admin/measurements/import?station_id=1", files=_csv_file(csv_content))

    m = db_session.execute(
        select(Measurement).where(
            Measurement.station_id == 1,
            Measurement.date_time == datetime(2026, 2, 21, 0, 0, 0),
        )
    ).scalars().first()
    if m is None:
        m = db_session.execute(
            select(Measurement).where(Measurement.station_id == 1)
            .order_by(Measurement.date_time)
        ).scalars().first()
    assert m is not None
    assert m.value != 99.99


def test_import_csv_station_not_found(client, seed_data):
    csv_content = "date_time,value\n2026-01-01T00:00:00,3.0\n"
    r = client.post(
        "/admin/measurements/import?station_id=999",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 404


def test_import_csv_wrong_extension_rejected(client, seed_data):
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files={"file": ("mediciones.txt", b"date_time,value\n2026-01-01T00:00:00,3.0\n", "text/plain")},
    )
    assert r.status_code == 422


def test_import_csv_wrong_header_rejected(client, seed_data):
    csv_content = "timestamp,nivel\n2026-01-01T00:00:00,3.0\n"
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 422
    assert "Cabecera inválida" in r.json()["detail"]


def test_import_csv_extra_columns_rejected(client, seed_data):
    csv_content = "date_time,value,extra\n2026-01-01T00:00:00,3.0,foo\n"
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 422


def test_import_csv_invalid_datetime_format_rejected(client, seed_data):
    csv_content = "date_time,value\n01/01/2026 00:00,3.0\n"
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["errors"]
    assert "Fila 2" in detail["errors"][0]


def test_import_csv_invalid_value_rejected(client, seed_data):
    csv_content = "date_time,value\n2026-01-01T00:00:00,abc\n"
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["errors"]
    assert "Fila 2" in detail["errors"][0]


def test_import_csv_one_bad_row_rejects_entire_file(client, seed_data, db_session):
    from sqlalchemy import select
    from common.models import Measurement

    before = db_session.execute(select(Measurement).where(Measurement.station_id == 1)).scalars().all()

    csv_content = (
        "date_time,value\n"
        "2026-01-01T00:00:00,3.0\n"
        "2026-01-02T00:00:00,MALO\n"
        "2026-01-03T00:00:00,3.5\n"
    )
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(csv_content),
    )
    assert r.status_code == 422

    after = db_session.execute(select(Measurement).where(Measurement.station_id == 1)).scalars().all()
    assert len(before) == len(after)


def test_import_csv_empty_file_rejected(client, seed_data):
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file(""),
    )
    assert r.status_code == 422


def test_import_csv_only_header_no_rows(client, seed_data):
    r = client.post(
        "/admin/measurements/import?station_id=1",
        files=_csv_file("date_time,value\n"),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["inserted"] == 0
    assert data["skipped"] == 0


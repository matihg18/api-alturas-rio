import csv
import io
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, asc
from common.models import Station, GaugePoint, GaugeDatum, ReferenceZeroType, Measurement
from api.admin_schemas import (
    GaugePointCreate,
    GaugePointUpdate,
    GaugePointAdminResponse,
    DatumTypeCreate,
    DatumTypeUpdate,
    DatumTypeAdminResponse,
    OffsetCreate,
    OffsetUpdate,
    OffsetAdminResponse,
    StationAssignGaugePoint,
    StationVisibilityUpdate,
    StationCoordinatesUpdate,
    StationAdminResponse,
    MeasurementImportResult,
)
from api.dependencies import get_db

router = APIRouter()
# ── Stations ─────────────────────────────────────────────────────────────────


@router.get("/stations", response_model=List[StationAdminResponse])
def admin_list_stations(db: Session = Depends(get_db)):
    """Lista todas las estaciones con su gauge point asignado."""
    stmt = select(Station).order_by(Station.name)
    return db.execute(stmt).scalars().all()


@router.put("/stations/{station_id}/gauge-point", response_model=StationAdminResponse)
def admin_assign_gauge_point(
    station_id: int,
    body: StationAssignGaugePoint,
    db: Session = Depends(get_db),
):
    """Asigna (o desasigna) un gauge point a una estación."""
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    if body.gauge_point_id is not None:
        gp = db.get(GaugePoint, body.gauge_point_id)
        if not gp:
            raise HTTPException(
                status_code=404, detail=f"GaugePoint {body.gauge_point_id} not found"
            )

    station.gauge_point_id = body.gauge_point_id
    db.commit()
    db.refresh(station)
    return station


@router.patch("/stations/{station_id}/visibility", response_model=StationAdminResponse)
def admin_toggle_station_visibility(
    station_id: int,
    body: StationVisibilityUpdate,
    db: Session = Depends(get_db),
):
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    station.is_visible = body.is_visible
    db.commit()
    db.refresh(station)
    return station


@router.patch("/stations/{station_id}/coordinates", response_model=StationAdminResponse)
def admin_update_station_coordinates(
    station_id: int,
    body: StationCoordinatesUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza las coordenadas geográficas de una estación."""
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    station.latitud = body.latitud
    station.longitud = body.longitud
    db.commit()
    db.refresh(station)
    return station


# ── Gauge Points ─────────────────────────────────────────────────────────────

@router.get("/gauge-points", response_model=List[GaugePointAdminResponse])
def admin_list_gauge_points(db: Session = Depends(get_db)):
    stmt = select(GaugePoint).order_by(GaugePoint.name)
    return db.execute(stmt).scalars().all()


@router.post("/gauge-points", response_model=GaugePointAdminResponse, status_code=201)
def admin_create_gauge_point(body: GaugePointCreate, db: Session = Depends(get_db)):
    gp = GaugePoint(name=body.name, river=body.river, description=body.description)
    db.add(gp)
    db.commit()
    db.refresh(gp)
    return gp


@router.put("/gauge-points/{gauge_point_id}", response_model=GaugePointAdminResponse)
def admin_update_gauge_point(
    gauge_point_id: int, body: GaugePointUpdate, db: Session = Depends(get_db)
):
    gp = db.get(GaugePoint, gauge_point_id)
    if not gp:
        raise HTTPException(status_code=404, detail=f"GaugePoint {gauge_point_id} not found")

    if body.name is not None:
        gp.name = body.name
    if body.river is not None:
        gp.river = body.river
    if body.description is not None:
        gp.description = body.description

    db.commit()
    db.refresh(gp)
    return gp


@router.delete("/gauge-points/{gauge_point_id}", status_code=204)
def admin_delete_gauge_point(gauge_point_id: int, db: Session = Depends(get_db)):
    gp = db.get(GaugePoint, gauge_point_id)
    if not gp:
        raise HTTPException(status_code=404, detail=f"GaugePoint {gauge_point_id} not found")
    db.delete(gp)
    db.commit()


# ── Datum Types ───────────────────────────────────────────────────────────────

@router.get("/datum-types", response_model=List[DatumTypeAdminResponse])
def admin_list_datum_types(db: Session = Depends(get_db)):
    stmt = select(ReferenceZeroType).order_by(ReferenceZeroType.code)
    return db.execute(stmt).scalars().all()


@router.post("/datum-types", response_model=DatumTypeAdminResponse, status_code=201)
def admin_create_datum_type(body: DatumTypeCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(ReferenceZeroType).where(ReferenceZeroType.code == body.code.upper())
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Datum type with code '{body.code}' already exists"
        )
    dt = ReferenceZeroType(
        code=body.code.upper(), name=body.name, description=body.description
    )
    db.add(dt)
    db.commit()
    db.refresh(dt)
    return dt


@router.put("/datum-types/{datum_type_id}", response_model=DatumTypeAdminResponse)
def admin_update_datum_type(
    datum_type_id: int, body: DatumTypeUpdate, db: Session = Depends(get_db)
):
    dt = db.get(ReferenceZeroType, datum_type_id)
    if not dt:
        raise HTTPException(status_code=404, detail=f"DatumType {datum_type_id} not found")

    if body.name is not None:
        dt.name = body.name
    if body.description is not None:
        dt.description = body.description

    db.commit()
    db.refresh(dt)
    return dt


@router.delete("/datum-types/{datum_type_id}", status_code=204)
def admin_delete_datum_type(datum_type_id: int, db: Session = Depends(get_db)):
    dt = db.get(ReferenceZeroType, datum_type_id)
    if not dt:
        raise HTTPException(status_code=404, detail=f"DatumType {datum_type_id} not found")
    db.delete(dt)
    db.commit()


# ── Offsets (GaugeDatum) ─────────────────────────────────────────────────────

@router.get("/offsets", response_model=List[OffsetAdminResponse])
def admin_list_offsets(
    gauge_point_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    stmt = select(GaugeDatum)
    if gauge_point_id is not None:
        stmt = stmt.where(GaugeDatum.gauge_point_id == gauge_point_id)
    stmt = stmt.order_by(GaugeDatum.gauge_point_id, GaugeDatum.datum_type_id)
    return db.execute(stmt).scalars().all()


@router.post("/offsets", response_model=OffsetAdminResponse, status_code=201)
def admin_create_offset(body: OffsetCreate, db: Session = Depends(get_db)):
    if not db.get(GaugePoint, body.gauge_point_id):
        raise HTTPException(
            status_code=404, detail=f"GaugePoint {body.gauge_point_id} not found"
        )
    if not db.get(ReferenceZeroType, body.datum_type_id):
        raise HTTPException(
            status_code=404, detail=f"DatumType {body.datum_type_id} not found"
        )

    existing = db.execute(
        select(GaugeDatum).where(
            GaugeDatum.gauge_point_id == body.gauge_point_id,
            GaugeDatum.datum_type_id == body.datum_type_id,
        )
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An offset for this gauge_point + datum_type combination already exists",
        )

    offset = GaugeDatum(
        gauge_point_id=body.gauge_point_id,
        datum_type_id=body.datum_type_id,
        offset_local_to_datum=body.offset_local_to_datum,
    )
    db.add(offset)
    db.commit()
    db.refresh(offset)
    return offset


@router.put("/offsets/{offset_id}", response_model=OffsetAdminResponse)
def admin_update_offset(
    offset_id: int, body: OffsetUpdate, db: Session = Depends(get_db)
):
    offset = db.get(GaugeDatum, offset_id)
    if not offset:
        raise HTTPException(status_code=404, detail=f"Offset {offset_id} not found")

    offset.offset_local_to_datum = body.offset_local_to_datum
    db.commit()
    db.refresh(offset)
    return offset


@router.delete("/offsets/{offset_id}", status_code=204)
def admin_delete_offset(offset_id: int, db: Session = Depends(get_db)):
    offset = db.get(GaugeDatum, offset_id)
    if not offset:
        raise HTTPException(status_code=404, detail=f"Offset {offset_id} not found")
    db.delete(offset)
    db.commit()


# ── Measurements Export ──────────────────────────────────────────────────────

@router.get("/measurements/export")
def admin_export_measurements_csv(
    station_id: int = Query(..., description="ID de la estación"),
    from_date: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    to_date: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    if from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail="from_date no puede ser posterior a to_date",
        )

    stmt = (
        select(Measurement)
        .where(Measurement.station_id == station_id)
        .where(Measurement.date_time >= from_date)
        .where(Measurement.date_time < (to_date + timedelta(days=1)))
        .order_by(asc(Measurement.date_time))
    )

    measurements = db.execute(stmt).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date_time", "value"])
    for m in measurements:
        writer.writerow([m.date_time.isoformat(), m.value])

    output.seek(0)

    safe_name = station.name.replace(' ', '_').replace('/', '-')
    filename = f"mediciones_{safe_name}_{station_id}_{from_date}_{to_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


EXPECTED_HEADER = ["date_time", "value"]
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"


@router.post("/measurements/import", response_model=MeasurementImportResult)
async def admin_import_measurements_csv(
    station_id: int = Query(..., description="ID de la estación destino"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(
            status_code=422,
            detail="El archivo debe tener extensión .csv",
        )

    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=422,
            detail="El archivo no es UTF-8 válido",
        )

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=422, detail="El archivo está vacío")

    header = [col.strip() for col in rows[0]]
    if header != EXPECTED_HEADER:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cabecera inválida: se esperaba `date_time,value`, "
                f"se recibió `{','.join(header)}`"
            ),
        )

    data_rows = [r for r in rows[1:] if any(cell.strip() for cell in r)]

    validation_errors: list[str] = []
    parsed: list[tuple[datetime, float]] = []

    for idx, row in enumerate(data_rows, start=2):
        if len(row) != 2:
            validation_errors.append(
                f"Fila {idx}: se esperaban 2 columnas, se encontraron {len(row)}"
            )
            continue

        raw_dt, raw_val = row[0].strip(), row[1].strip()

        try:
            dt = datetime.strptime(raw_dt, ISO_FORMAT)
        except ValueError:
            validation_errors.append(
                f"Fila {idx}: date_time `{raw_dt}` no tiene el formato esperado "
                f"(YYYY-MM-DDTHH:MM:SS)"
            )
            dt = None

        try:
            val = float(raw_val)
        except ValueError:
            validation_errors.append(
                f"Fila {idx}: value `{raw_val}` no es un número válido"
            )
            val = None

        if dt is not None and val is not None:
            parsed.append((dt, val))

    if validation_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "El CSV contiene errores de formato. No se insertó ninguna medición.",
                "errors": validation_errors,
            },
        )

    total = len(parsed)

    existing_stmt = select(Measurement.date_time).where(
        Measurement.station_id == station_id
    )
    existing_datetimes: set[datetime] = set(
        db.execute(existing_stmt).scalars().all()
    )

    new_measurements = [
        Measurement(station_id=station_id, date_time=dt, value=val)
        for dt, val in parsed
        if dt not in existing_datetimes
    ]

    inserted = len(new_measurements)
    skipped = total - inserted

    if new_measurements:
        db.add_all(new_measurements)
        db.commit()

    return MeasurementImportResult(total=total, inserted=inserted, skipped=skipped)

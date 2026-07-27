// ── Types ─────────────────────────────────────────────────────────────────

export interface Station {
  id: number;
  name: string;
  river: string;
  source: string;
  latitud: number | null;
  longitud: number | null;
  alert_value: number | null;
  evacuation_value: number | null;
  gauge_point_id: number | null;
  gauge_point: GaugePoint | null;
}

export interface GaugePoint {
  id: number;
  name: string;
  river: string | null;
  description: string | null;
}

export interface DatumType {
  id: number;
  code: string;
  name: string;
  description: string | null;
}

export interface Offset {
  id: number;
  gauge_point_id: number;
  datum_type_id: number;
  offset_local_to_datum: number;
  gauge_point: GaugePoint;
  datum_type: DatumType;
}

// ── Input types ───────────────────────────────────────────────────────────

export interface GaugePointCreate { name: string; river?: string; description?: string; }
export interface GaugePointUpdate { name?: string; river?: string; description?: string; }
export interface DatumTypeCreate  { code: string; name: string; description?: string; }
export interface DatumTypeUpdate  { name?: string; description?: string; }
export interface OffsetCreate     { gauge_point_id: number; datum_type_id: number; offset_local_to_datum: number; }
export interface OffsetUpdate     { offset_local_to_datum: number; }
export interface AssignGaugePoint { gauge_point_id: number | null; }

// ── Client ────────────────────────────────────────────────────────────────

const BASE = '/api/admin';

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch { /* noop */ }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Stations
export const api = {
  stations: {
    list:            ()                                    => request<Station[]>('GET', '/stations'),
    assignGaugePoint:(id: number, body: AssignGaugePoint) => request<Station>('PUT', `/stations/${id}/gauge-point`, body),
  },
  gaugePoints: {
    list:   ()                                  => request<GaugePoint[]>('GET', '/gauge-points'),
    create: (body: GaugePointCreate)            => request<GaugePoint>('POST', '/gauge-points', body),
    update: (id: number, body: GaugePointUpdate)=> request<GaugePoint>('PUT', `/gauge-points/${id}`, body),
    delete: (id: number)                        => request<void>('DELETE', `/gauge-points/${id}`),
  },
  datumTypes: {
    list:   ()                                  => request<DatumType[]>('GET', '/datum-types'),
    create: (body: DatumTypeCreate)             => request<DatumType>('POST', '/datum-types', body),
    update: (id: number, body: DatumTypeUpdate) => request<DatumType>('PUT', `/datum-types/${id}`, body),
    delete: (id: number)                        => request<void>('DELETE', `/datum-types/${id}`),
  },
  offsets: {
    list:   (gaugePointId?: number)            => request<Offset[]>('GET', gaugePointId ? `/offsets?gauge_point_id=${gaugePointId}` : '/offsets'),
    create: (body: OffsetCreate)               => request<Offset>('POST', '/offsets', body),
    update: (id: number, body: OffsetUpdate)   => request<Offset>('PUT', `/offsets/${id}`, body),
    delete: (id: number)                       => request<void>('DELETE', `/offsets/${id}`),
  },
};

// ──────────────────────────────────────────────────────────
// Tipos que reflejan exactamente los schemas del backend
// ──────────────────────────────────────────────────────────

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
}

export interface Measurement {
  id: number;
  station_id: number;
  date_time: string;   // ISO 8601
  value: number;       // metros (cero local u otro datum si se pidió conversión)
}

export interface LatestMeasurement extends Measurement {
  datum_used: string;
  conversion_available: boolean;
}

export interface PagedMeasurementResponse {
  total_count: number;
  datum_used: string;
  conversion_available: boolean;
  items: Measurement[];
}

export interface PagedStationsResponse {
  total_count: number;
  items: Station[];
}

export interface DatumType {
  id: number;
  code: string;   // p.ej. "IGN", "WHARTON"
  name: string;
  description: string | null;
}

export interface GaugeDatum {
  id: number;
  offset_local_to_datum: number;
  datum_type: DatumType;
}

export interface GaugePoint {
  id: number;
  name: string;
  river: string | null;
  description: string | null;
  datums: GaugeDatum[];
}

// ──────────────────────────────────────────────────────────
// Cliente de API  (sólo GET, sin datos de muestra)
// ──────────────────────────────────────────────────────────

const BASE = '/api';

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  /**
   * Devuelve TODAS las estaciones (itera la paginación si hubiera más de 100).
   */
  async getStations(): Promise<Station[]> {
    const first = await apiFetch<PagedStationsResponse>('/stations?limit=100&skip=0');
    const total = first.total_count;
    let items = first.items;

    // Si hay más páginas, las cargamos
    if (total > 100) {
      const pages = Math.ceil(total / 100);
      const rest = await Promise.all(
        Array.from({ length: pages - 1 }, (_, i) =>
          apiFetch<PagedStationsResponse>(`/stations?limit=100&skip=${(i + 1) * 100}`)
        )
      );
      for (const page of rest) items = items.concat(page.items);
    }

    return items;
  },

  /**
   * Devuelve la última medición registrada de la estación.
   * Si se indica `datumCode`, el servidor aplica la conversión al datum destino.
   */
  async getLatestMeasurement(
    stationId: number,
    datumCode?: string,
  ): Promise<LatestMeasurement> {
    const qs = datumCode ? `?datum=${encodeURIComponent(datumCode)}` : '';
    return apiFetch<LatestMeasurement>(`/measurements/latest/${stationId}${qs}`);
  },

  /**
   * Devuelve las últimas N mediciones en orden cronológico (más antiguo → más reciente).
   * Si se indica `datumCode`, el servidor aplica la conversión al datum destino.
   */
  async getMeasurements(
    stationId: number,
    limit = 100,
    skip = 0,
    datumCode?: string,
    fromDate?: string,
    toDate?: string,
  ): Promise<PagedMeasurementResponse> {
    let url = `/measurements/${stationId}?limit=${limit}&skip=${skip}&sorting=date_time-desc`;
    if (datumCode) url += `&datum=${encodeURIComponent(datumCode)}`;
    if (fromDate) url += `&from_date=${encodeURIComponent(fromDate)}`;
    if (toDate) url += `&to_date=${encodeURIComponent(toDate)}`;
    
    const result = await apiFetch<PagedMeasurementResponse>(url);
    // Invertimos para que el gráfico quede de izquierda (más antiguo) a derecha (más reciente)
    return { ...result, items: [...result.items].reverse() };
  },

  /**
   * Devuelve el GaugePoint (escalímetro) de la estación, incluyendo todos los
   * datums de conversión disponibles.  Lanza error si la estación no tiene
   * gauge point asignado (404).
   */
  async getGaugePoint(stationId: number): Promise<GaugePoint> {
    return apiFetch<GaugePoint>(`/datums/station/${stationId}`);
  },
};

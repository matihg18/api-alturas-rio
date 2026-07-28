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
  date_time: string;
  value: number;
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
  code: string;
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


const BASE = '/api';

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  async getStations(): Promise<Station[]> {
    const first = await apiFetch<PagedStationsResponse>('/stations?limit=100&skip=0');
    const total = first.total_count;
    let items = first.items;

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

  async getLatestMeasurement(
    stationId: number,
    datumCode?: string,
  ): Promise<LatestMeasurement> {
    const qs = datumCode ? `?datum=${encodeURIComponent(datumCode)}` : '';
    return apiFetch<LatestMeasurement>(`/measurements/latest/${stationId}${qs}`);
  },

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
    return { ...result, items: [...result.items].reverse() };
  },

  async getGaugePoint(stationId: number): Promise<GaugePoint> {
    return apiFetch<GaugePoint>(`/datums/station/${stationId}`);
  },
};

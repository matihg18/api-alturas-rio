import { useState, useEffect, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';
import { BarChart2, Layers } from 'lucide-react';
import { apiClient, type Station, type LatestMeasurement } from '../services/api';

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export type Trend = 'up' | 'down' | 'stable' | 'none';

function makeTrendIcon(trend: Trend): L.DivIcon {
  const configs: Record<Trend, { symbol: string; bg: string; border: string }> = {
    up: { symbol: '▲', bg: '#dc2626', border: '#b91c1c' },
    down: { symbol: '▼', bg: '#16a34a', border: '#15803d' },
    stable: { symbol: '=', bg: '#2563eb', border: '#1d4ed8' },
    none: { symbol: '✕', bg: '#94a3b8', border: '#64748b' },
  };
  const { symbol, bg, border } = configs[trend];

  const html = `<div class="trend-marker" style="background:${bg};border-color:${border};">${symbol}</div>`;

  return L.divIcon({
    html,
    className: 'trend-marker-wrapper',
    iconSize: [25, 25],
    iconAnchor: [12, 12],
    popupAnchor: [0, -17],
  });
}

function BoundsFitter({ stations }: { stations: Station[] }) {
  const map = useMap();
  const prevCount = useRef<number | null>(null);

  useEffect(() => {
    const coords = stations
      .filter((s) => s.latitud != null && s.longitud != null)
      .map((s) => [s.latitud!, s.longitud!] as [number, number]);

    if (coords.length === 0) return;

    if (prevCount.current !== coords.length) {
      if (coords.length === 1) {
        map.setView(coords[0], 10);
      } else {
        map.fitBounds(L.latLngBounds(coords), { padding: [48, 48] });
      }
      prevCount.current = coords.length;
    }
  }, [map, stations]);

  return null;
}

interface StationPopupProps {
  station: Station;
  latest: LatestMeasurement | null;
  activeSeries: string | null;
}

function StationPopup({ station, latest, activeSeries }: StationPopupProps) {
  const navigate = useNavigate();
  const [latestFlow, setLatestFlow] = useState<number | null>(null);
  const [loadingFlow, setLoadingFlow] = useState(false);

  const hasFlow = (station.available_series ?? []).includes('flow');

  useEffect(() => {
    let isMounted = true;
    if (hasFlow) {
      setLoadingFlow(true);
      apiClient
        .getLatestFlow(station.id)
        .then((res) => {
          if (isMounted) setLatestFlow(res.flow);
        })
        .catch(() => {
          if (isMounted) setLatestFlow(null);
        })
        .finally(() => {
          if (isMounted) setLoadingFlow(false);
        });
    }
    return () => {
      isMounted = false;
    };
  }, [station.id, hasFlow]);

  const formattedDate = latest?.date_time
    ? new Date(latest.date_time).toLocaleString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
    : null;

  return (
    <div className="map-popup">
      <div className="map-popup__header">
        <div className="map-popup__name">{station.name}</div>
        <div className="map-popup__river">Río {station.river}</div>
        <div className="map-popup__series-tags">
          {(station.available_series ?? []).map((s) => (
            <span key={s} className={`popup-series-tag popup-series-tag--${s}`}>
              {s === 'level' ? 'Nivel' : s === 'flow' ? 'Caudal' : s}
            </span>
          ))}
        </div>
      </div>

      <div className="map-popup__body">
        <div className="map-popup__source-row">
          <span className="map-popup__last-label">Fuente</span>
          <span className="map-popup__source">{station.source}</span>
        </div>
        <div className="map-popup__divider" />

        {(activeSeries === null || activeSeries === 'level') && (
          <div
            className={`map-popup__metric${hasFlow ? ' map-popup__metric--clickable' : ''}`}
            onClick={() => navigate('/dashboard', { state: { stationId: station.id, series: 'level' } })}
            title="Ver detalle de Nivel en Dashboard"
          >
            <div className="map-popup__last-label">Último Nivel</div>
            {latest?.value != null ? (
              <div className="map-popup__value mono">{latest.value.toFixed(2)} m</div>
            ) : (
              <div className="map-popup__no-value">Sin datos de nivel</div>
            )}
          </div>
        )}

        {hasFlow && (activeSeries === null || activeSeries === 'flow') && (
          <div
            className="map-popup__metric map-popup__metric--clickable"
            onClick={() => navigate('/dashboard', { state: { stationId: station.id, series: 'flow' } })}
            title="Ver detalle de Caudal en Dashboard"
          >
            <div className="map-popup__last-label">Último Caudal</div>
            {loadingFlow ? (
              <div className="map-popup__no-value">Cargando caudal…</div>
            ) : latestFlow != null ? (
              <div className="map-popup__value mono map-popup__value--flow">
                {latestFlow.toLocaleString('es-AR', { maximumFractionDigits: 1 })} m³/s
              </div>
            ) : (
              <div className="map-popup__no-value">Sin datos de caudal</div>
            )}
          </div>
        )}

        {formattedDate && <div className="map-popup__date">{formattedDate}</div>}
      </div>

      <div className="map-popup__footer">
        {hasFlow && activeSeries === null ? (
          <div className="map-popup__footer-btns">
            <button
              className="map-popup__btn"
              onClick={() => navigate('/dashboard', { state: { stationId: station.id, series: 'level' } })}
            >
              <BarChart2 size={12} />
              Ver Nivel
            </button>
            <button
              className="map-popup__btn map-popup__btn--flow"
              onClick={() => navigate('/dashboard', { state: { stationId: station.id, series: 'flow' } })}
            >
              <BarChart2 size={12} />
              Ver Caudal
            </button>
          </div>
        ) : (
          <button
            className={`map-popup__btn${activeSeries === 'flow' ? ' map-popup__btn--flow' : ''}`}
            onClick={() =>
              navigate('/dashboard', {
                state: { stationId: station.id, series: activeSeries ?? 'level' },
              })
            }
          >
            <BarChart2 size={12} />
            Ver detalle {activeSeries === 'flow' ? 'de Caudal' : activeSeries === 'level' ? 'de Nivel' : ''}
          </button>
        )}
      </div>
    </div>
  );
}

export interface StationWithLatest extends Station {
  latest: LatestMeasurement | null;
  trend: Trend;
}

interface StationMapProps {
  stations: StationWithLatest[];
}

const ARGENTINA_CENTER: [number, number] = [-34.6, -64.2];

const SERIES_LABELS: Record<string, string> = {
  level: 'Nivel',
  flow: 'Caudal',
};

export function StationMap({ stations }: StationMapProps) {
  const [seriesFilter, setSeriesFilter] = useState<string | null>(null);

  const availableSeriesGlobal = useMemo(() => {
    const set = new Set<string>();
    stations.forEach((s) => (s.available_series ?? []).forEach((sr) => set.add(sr)));
    return Array.from(set);
  }, [stations]);

  const filteredStations = useMemo(() => {
    return stations.filter((s) => {
      if (s.latitud == null || s.longitud == null) return false;
      if (seriesFilter === null) return true;
      return (s.available_series ?? []).includes(seriesFilter);
    });
  }, [stations, seriesFilter]);

  return (
    <div className="map-container-wrapper">
      {availableSeriesGlobal.length > 1 && (
        <div className="map-series-overlay">
          <span className="map-series-overlay__label">
            <Layers size={13} />
            Serie:
          </span>
          <div className="map-series-overlay__pills">
            <button
              className={`series-pill${seriesFilter === null ? ' series-pill--active' : ''}`}
              onClick={() => setSeriesFilter(null)}
            >
              Todas ({stations.filter((s) => s.latitud != null && s.longitud != null).length})
            </button>
            {availableSeriesGlobal.map((s) => {
              const count = stations.filter(
                (st) =>
                  st.latitud != null &&
                  st.longitud != null &&
                  (st.available_series ?? []).includes(s),
              ).length;
              return (
                <button
                  key={s}
                  className={`series-pill${seriesFilter === s ? ' series-pill--active' : ''}`}
                  onClick={() => setSeriesFilter(seriesFilter === s ? null : s)}
                >
                  {SERIES_LABELS[s] ?? s} ({count})
                </button>
              );
            })}
          </div>
        </div>
      )}

      <MapContainer
        center={ARGENTINA_CENTER}
        zoom={5}
        className="map-fill"
        scrollWheelZoom
      >
        <TileLayer
          url={`https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${import.meta.env.VITE_CARTO_API_KEY}`}
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          maxZoom={19}
        />

        <BoundsFitter stations={filteredStations} />

        {filteredStations.map((s) => (
          <Marker
            key={s.id}
            position={[s.latitud!, s.longitud!]}
            icon={makeTrendIcon(s.trend)}
          >
            <Popup minWidth={220} maxWidth={280}>
              <StationPopup station={s} latest={s.latest} activeSeries={seriesFilter} />
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}


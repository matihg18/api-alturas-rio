import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';
import { BarChart2 } from 'lucide-react';
import type { Station, LatestMeasurement } from '../services/api';

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
  const fitted = useRef(false);

  useEffect(() => {
    if (fitted.current) return;

    const coords = stations
      .filter((s) => s.latitud != null && s.longitud != null)
      .map((s) => [s.latitud!, s.longitud!] as [number, number]);

    if (coords.length === 0) return;

    if (coords.length === 1) {
      map.setView(coords[0], 10);
    } else {
      map.fitBounds(L.latLngBounds(coords), { padding: [48, 48] });
    }

    fitted.current = true;
  }, [map, stations]);

  return null;
}

interface StationPopupProps {
  station: Station;
  latest: LatestMeasurement | null;
}

function StationPopup({ station, latest }: StationPopupProps) {
  const navigate = useNavigate();

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
      </div>

      <div className="map-popup__body">
        <div className="map-popup__source-row">
          <span className="map-popup__last-label">Fuente</span>
          <span className="map-popup__source">{station.source}</span>
        </div>
        <div className="map-popup__divider" />
        <div className="map-popup__last-label">Última medición</div>
        {latest?.value != null ? (
          <>
            <div className="map-popup__value mono">{latest.value.toFixed(2)} m</div>
            {formattedDate && (
              <div className="map-popup__date">{formattedDate}</div>
            )}
          </>
        ) : (
          <div className="map-popup__no-value">Sin datos recientes</div>
        )}
      </div>

      <div className="map-popup__footer">
        <button
          className="map-popup__btn"
          onClick={() => navigate('/dashboard', { state: { stationId: station.id } })}
        >
          <BarChart2 size={12} />
          Ver detalle completo
        </button>
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

export function StationMap({ stations }: StationMapProps) {
  const withCoords = stations.filter(
    (s) => s.latitud != null && s.longitud != null,
  );

  return (
    <MapContainer
      center={ARGENTINA_CENTER}
      zoom={5}
      className="map-fill"
      scrollWheelZoom
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        subdomains="abcd"
        maxZoom={19}
      />

      <BoundsFitter stations={withCoords} />

      {withCoords.map((s) => (
        <Marker
          key={s.id}
          position={[s.latitud!, s.longitud!]}
          icon={makeTrendIcon(s.trend)}
        >
          <Popup minWidth={220} maxWidth={280}>
            <StationPopup station={s} latest={s.latest} />
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

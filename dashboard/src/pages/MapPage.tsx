import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import type { Station, LatestMeasurement } from '../services/api';
import { StationMap } from '../components/StationMap';
import type { StationWithLatest } from '../components/StationMap';
import {
  Droplet,
  RefreshCw,
  AlertTriangle,
  Layers,
  ArrowRight,
} from 'lucide-react';

type Status = 'loading' | 'error' | 'ok';

export function MapPage() {
  const navigate = useNavigate();
  const [stations, setStations] = useState<StationWithLatest[]>([]);
  const [status, setStatus] = useState<Status>('loading');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const load = useCallback(async (silent = false) => {
    if (!silent) setStatus('loading');
    else setIsRefreshing(true);
    try {
      const list: Station[] = await apiClient.getStations();
      const withLatest: StationWithLatest[] = await Promise.all(
        list.map(async (s) => {
          try {
            const latest: LatestMeasurement = await apiClient.getLatestMeasurement(s.id);
            return { ...s, latest };
          } catch {
            return { ...s, latest: null };
          }
        }),
      );
      setStations(withLatest);
      setStatus('ok');
    } catch {
      setStatus('error');
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(() => load(true), 60_000);
    return () => clearInterval(id);
  }, [load]);

  const withCoords = stations.filter((s) => s.latitud != null && s.longitud != null);

  return (
    <div className="map-page">
      <header className="map-page__header">
        <div className="map-page__brand">
          <Droplet size={20} className="map-page__brand-icon" />
          <div>
            <div className="map-page__title">Sistema de Monitoreo de Ríos</div>
            <a
              href="https://frcu.utn.edu.ar/geru"
              target="_blank"
              rel="noopener noreferrer"
              className="map-page__subtitle"
            >
              Grupo de Estudio del Río Uruguay - UTN FRCU
            </a>
          </div>
        </div>

        <div className="map-page__actions">
          <button
            className="btn-icon"
            onClick={() => load(true)}
            disabled={isRefreshing || status === 'loading'}
            title="Actualizar datos"
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
          </button>
          <button
            id="go-to-dashboard-btn"
            className="btn"
            onClick={() => navigate('/dashboard')}
          >
            <Layers size={14} />
            Ver listado de estaciones
            <ArrowRight size={13} />
          </button>
        </div>
      </header>

      <div className="map-page__body">
        {status === 'loading' ? (
          <div className="map-page__state">
            <div className="spinner" />
            <p>Cargando datos hidrológicos…</p>
          </div>
        ) : status === 'error' ? (
          <div className="map-page__state">
            <AlertTriangle size={28} style={{ color: '#ef4444', marginBottom: '0.5rem' }} />
            <p style={{ color: '#ef4444', fontWeight: 600 }}>Error de conectividad</p>
            <p style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>
              No se pudo establecer conexión con el servidor de datos.
            </p>
            <button className="btn" style={{ marginTop: '1rem' }} onClick={() => load()}>
              Reintentar
            </button>
          </div>
        ) : (
          <StationMap stations={withCoords} />
        )}
      </div>

      <footer className="map-page__disclaimer">
        <span>
          Los datos hidrológicos son recopilados de fuentes oficiales:{' '}
          <a href="https://contenidosweb.prefecturanaval.gob.ar/alturas/" target="_blank" rel="noopener noreferrer">Prefectura Naval Argentina</a>,{' '}
          <a href="https://alerta.ina.gob.ar" target="_blank" rel="noopener noreferrer">INA</a>,{' '}
          <a href="http://www.caru.org.ar" target="_blank" rel="noopener noreferrer">CARU</a> y{' '}
          <a href="https://gualeguaychu.gov.ar/alturadelrio" target="_blank" rel="noopener noreferrer">Municipalidad de Gualeguaychú</a>.
          {' '}Esta plataforma expone el conjunto de datos con fines informativos.
          La exactitud o vigencia de los datos es responsabilidad de cada organismo fuente.
        </span>
      </footer>
    </div>
  );
}

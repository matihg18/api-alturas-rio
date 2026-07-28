import { useState, useEffect, useCallback } from 'react';
import { apiClient, Station, Measurement, LatestMeasurement } from './services/api';
import { StationDetail } from './components/StationDetail';
import {
  Droplet,
  RefreshCw,
  AlertTriangle,
  X,
  Menu,
} from 'lucide-react';


interface StationWithLatest extends Station {
  latest: LatestMeasurement | null;
}

type AppStatus = 'loading' | 'error' | 'ok';

function App() {
  const [stations, setStations] = useState<StationWithLatest[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<number | null>(null);
  const [history, setHistory] = useState<Measurement[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [status, setStatus] = useState<AppStatus>('loading');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const fetchStations = useCallback(async (silent = false) => {
    if (!silent) setStatus('loading');
    else setIsRefreshing(true);
    try {
      const stationList = await apiClient.getStations();
      const withLatest: StationWithLatest[] = await Promise.all(
        stationList.map(async (s) => {
          try { return { ...s, latest: await apiClient.getLatestMeasurement(s.id) }; }
          catch { return { ...s, latest: null }; }
        })
      );
      setStations(withLatest);
      setErrorMsg('');
      setStatus('ok');
      setSelectedStationId((prev) => {
        if (prev !== null && withLatest.find((s) => s.id === prev)) return prev;
        const first = withLatest.find((s) => s.latest !== null) ?? withLatest[0];
        return first ? first.id : prev;
      });
    } catch {
      setErrorMsg('No se pudo establecer conexión con el servidor de datos.');
      setStatus('error');
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const fetchHistory = useCallback(async (stationId: number) => {
    try {
      const result = await apiClient.getMeasurements(stationId);
      setHistory(result.items);
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    fetchStations();
    const interval = setInterval(() => fetchStations(true), 60_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedStationId !== null) fetchHistory(selectedStationId);
  }, [selectedStationId, fetchHistory]);

  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1025px)');
    const handler = (e: MediaQueryListEvent) => { if (e.matches) setSidebarOpen(false); };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const handleSelectStation = (id: number) => {
    setSelectedStationId(id);
    setSidebarOpen(false);
  };

  const filteredStations = stations.filter(
    (s) => s.name.toLowerCase().includes(searchQuery.toLowerCase())
      || s.river.toLowerCase().includes(searchQuery.toLowerCase())
  );


  const selectedStation = stations.find((s) => s.id === selectedStationId) ?? null;

  return (
    <>
      <div className="mobile-topbar">
        <button
          className="mobile-topbar__btn"
          onClick={() => setSidebarOpen((o) => !o)}
          aria-label={sidebarOpen ? 'Cerrar menú' : 'Abrir menú'}
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span className="mobile-topbar__logo"><Droplet size={16} /></span>
        <span className="mobile-topbar__title">Sistema de Monitoreo de Ríos</span>
        {selectedStation && (
          <span className="mobile-topbar__station">{selectedStation.name}</span>
        )}
      </div>

      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      )}
      <div className="app-layout">
        <aside className={`app-sidebar${sidebarOpen ? ' is-open' : ''}`}>

          <div className="sidebar-header">
            <div className="sidebar-header__row">
              <Droplet size={20} className="sidebar-header__icon" />
              <div>
                <h1 className="sidebar-header__title">
                  Sistema de Monitoreo de Ríos
                </h1>
                <a
                  href="https://frcu.utn.edu.ar/geru"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sidebar-header__subtitle sidebar-header__link"
                >
                  Grupo de Estudio del Río Uruguay
                </a>
              </div>
            </div>

            <div className="sidebar-status sidebar-status--end">
              <button
                onClick={() => fetchStations()}
                disabled={isRefreshing || status === 'loading'}
                title="Sincronizar datos"
                className="btn-icon"
              >
                <RefreshCw size={12} className={isRefreshing ? 'spin' : ''} />
              </button>
            </div>
          </div>
          <div className="sidebar-search">
            <div className="sidebar-search__inner">
              <input
                type="text"
                placeholder="Buscar estación..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="sidebar-search__input"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="sidebar-search__clear">
                  <X size={12} />
                </button>
              )}
            </div>
          </div>

          <div className="station-list">
            {status === 'loading' ? (
              <div className="station-list__empty">Cargando estaciones…</div>
            ) : filteredStations.length === 0 ? (
              <div className="station-list__empty">No se encontraron estaciones</div>
            ) : (
              <div className="station-list__items">
                {filteredStations.map((station) => {
                  const isSelected = station.id === selectedStationId;
                  return (
                    <button
                      key={station.id}
                      onClick={() => handleSelectStation(station.id)}
                      className={`station-item${isSelected ? ' station-item--selected' : ''}`}
                    >
                      <div>
                        <div className="station-item__name">
                          {station.name}
                        </div>
                        <div className="station-item__river">
                          Río {station.river}
                        </div>
                      </div>
                      <div>
                        {station.latest?.value != null ? (
                          <span className="mono station-item__value">
                            {station.latest.value.toFixed(2)}m
                          </span>
                        ) : (
                          <span className="station-item__no-value">—</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </aside>
        <main className="app-main">
          {status === 'loading' ? (
            <div className="main-loading">
              <div className="spinner" />
              <p className="main-loading__text">Cargando datos hidrológicos…</p>
            </div>
          ) : status === 'error' ? (
            <div className="card-panel error-panel">
              <AlertTriangle size={28} className="error-panel__icon" />
              <h2 className="error-panel__title">Error de Conectividad</h2>
              <p className="error-panel__msg">{errorMsg}</p>
              <button className="btn" onClick={() => fetchStations()}>Reintentar enlace</button>
            </div>
          ) : selectedStation ? (
            <StationDetail station={selectedStation} latest={selectedStation.latest} history={history} />
          ) : (
            <div className="card-panel empty-panel">
              Seleccione una estación de la lista para ver los datos de telemetría.
            </div>
          )}
        </main>
      </div>
    </>
  );
}

export default App;

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
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedStationId !== null) fetchHistory(selectedStationId);
  }, [selectedStationId, fetchHistory]);

  // Cerrar sidebar si se pasa a desktop
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
      {/* ── Top bar (visible solo en móvil via CSS) ─────── */}
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

      {/* ── Backdrop del drawer ─────────────────────────── */}
      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      )}

      {/* ── Layout principal ────────────────────────────── */}
      <div className="app-layout">

        {/* Sidebar / Drawer */}
        <aside className={`app-sidebar${sidebarOpen ? ' is-open' : ''}`}>

          {/* Header del sidebar */}
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(17,24,39,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <Droplet size={20} style={{ color: 'var(--accent-blue)' }} />
              <div>
                <h1 style={{ fontSize: '1.05rem', fontWeight: '600', letterSpacing: '-0.01em' }}>
                  Sistema de Monitoreo de Ríos
                </h1>
                <a
                  href="https://frcu.utn.edu.ar/geru"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', fontWeight: '500', textDecoration: 'none', transition: 'color 0.15s' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--accent-blue)')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
                >
                  Grupo de Estudio del Río Uruguay
                </a>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.8rem' }}>
              <button
                onClick={() => fetchStations()}
                disabled={isRefreshing || status === 'loading'}
                title="Sincronizar datos"
                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '0.2rem', borderRadius: '2px' }}
              >
                <RefreshCw size={12} className={isRefreshing ? 'spin' : ''} />
              </button>
            </div>
          </div>

          {/* Buscador */}
          <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Buscar estación..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ width: '100%', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '3px', padding: '0.4rem 2rem 0.4rem 0.6rem', color: 'var(--text-primary)', fontSize: '0.8rem', outline: 'none' }}
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} style={{ position: 'absolute', right: '0.5rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '0.2rem' }}>
                  <X size={12} />
                </button>
              )}
            </div>
          </div>

          {/* Lista de estaciones */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
            {status === 'loading' ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>Cargando estaciones…</div>
            ) : filteredStations.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>No se encontraron estaciones</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                {filteredStations.map((station) => {
                  const isSelected = station.id === selectedStationId;
                  return (
                    <button
                      key={station.id}
                      onClick={() => handleSelectStation(station.id)}
                      style={{
                        background: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                        border: 'none',
                        borderLeft: isSelected ? '3px solid var(--accent-blue)' : '3px solid transparent',
                        borderRadius: '3px',
                        padding: '0.6rem 0.8rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        width: '100%',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'background 0.1s',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: isSelected ? '600' : '400', fontSize: '0.8rem', color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                          {station.name}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                          Río {station.river}
                        </div>
                      </div>
                      <div>
                        {station.latest?.value != null ? (
                          <span className="mono" style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                            {station.latest.value.toFixed(2)}m
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>—</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </aside>

        {/* ── Contenido principal ──────────────────────── */}
        <main className="app-main">
          {status === 'loading' ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.8rem', color: 'var(--text-secondary)' }}>
              <div style={{ width: '24px', height: '24px', border: '2px solid var(--border-color)', borderTopColor: 'var(--accent-blue)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <p style={{ fontSize: '0.75rem' }}>Cargando datos hidrológicos…</p>
            </div>
          ) : status === 'error' ? (
            <div className="card-panel" style={{ margin: 'auto', maxWidth: '500px', textAlign: 'center', borderColor: 'rgba(239,68,68,0.4)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <AlertTriangle size={28} style={{ color: 'red', margin: '0 auto' }} />
              <h2 style={{ fontSize: '1.1rem', color: 'red', fontWeight: '600' }}>Error de Conectividad</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{errorMsg}</p>
              <button className="btn" onClick={() => fetchStations()}>Reintentar enlace</button>
            </div>
          ) : selectedStation ? (
            <StationDetail station={selectedStation} latest={selectedStation.latest} history={history} />
          ) : (
            <div className="card-panel" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Seleccione una estación de la lista para ver los datos de telemetría.
            </div>
          )}
        </main>
      </div>
    </>
  );
}

export default App;

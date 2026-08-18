import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { apiClient, Station, Measurement, LatestMeasurement } from './services/api';
import { StationDetail } from './components/StationDetail';
import { SourcesFooter } from './components/SourcesFooter';
import { useLocation } from 'react-router-dom';
import {
  Droplet,
  AlertTriangle,
  X,
  Menu,
} from 'lucide-react';


interface StationWithLatest extends Station {
  latest: LatestMeasurement | null;
}

type AppStatus = 'loading' | 'error' | 'ok';

function App() {
  const location = useLocation();
  const requestedId = (location.state as { stationId?: number } | null)?.stationId ?? null;

  const [stations, setStations] = useState<StationWithLatest[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<number | null>(requestedId);
  const [history, setHistory] = useState<Measurement[]>([]);
  const [stationSearch, setStationSearch] = useState('');
  const [riverFilter, setRiverFilter] = useState('');
  const [riverInput, setRiverInput] = useState('');
  const [riverDropdownOpen, setRiverDropdownOpen] = useState(false);
  const riverComboboxRef = useRef<HTMLDivElement>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [status, setStatus] = useState<AppStatus>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  const listRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<Map<number, HTMLButtonElement>>(new Map());

  useEffect(() => {
    if (selectedStationId === null) return;
    const t = setTimeout(() => {
      const list = listRef.current;
      const el = itemRefs.current.get(selectedStationId);
      if (!list || !el) return;
      list.scrollTop = el.offsetTop - list.offsetTop - 8;
    }, 80);
    return () => clearTimeout(t);
  }, [selectedStationId, stations]);

  const fetchStations = useCallback(async (silent = false) => {
    if (!silent) setStatus('loading');
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

  // Unique sorted list of rivers
  const uniqueRivers = useMemo(() => {
    const set = new Set(stations.map((s) => s.river));
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'es'));
  }, [stations]);

  // Rivers shown in dropdown: all if empty input, else prefix matches first then internal matches
  const dropdownRivers = useMemo(() => {
    if (!riverInput.trim()) return uniqueRivers;
    const q = riverInput.toLowerCase();
    const prefix = uniqueRivers.filter((r) => r.toLowerCase().startsWith(q));
    const internal = uniqueRivers.filter(
      (r) => !r.toLowerCase().startsWith(q) && r.toLowerCase().includes(q)
    );
    return [...prefix, ...internal];
  }, [uniqueRivers, riverInput]);

  // Close river dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (riverComboboxRef.current && !riverComboboxRef.current.contains(e.target as Node)) {
        setRiverDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectRiver = (river: string) => {
    setRiverFilter(river);
    setRiverInput(river);
    setRiverDropdownOpen(false);
  };

  const handleClearRiver = () => {
    setRiverFilter('');
    setRiverInput('');
    setRiverDropdownOpen(false);
  };

  const filteredStations = stations.filter((s) => {
    const matchName = s.name.toLowerCase().includes(stationSearch.toLowerCase());
    const matchRiver = riverInput.trim() === '' ||
      s.river.toLowerCase().includes(riverInput.toLowerCase());
    return matchName && matchRiver;
  });


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
          </div>
          <div className="sidebar-search">
            {/* Filtro por nombre de estación */}
            <div className="sidebar-search__inner">
              <input
                type="text"
                placeholder="Buscar por nombre de estación…"
                value={stationSearch}
                onChange={(e) => setStationSearch(e.target.value)}
                className="sidebar-search__input"
              />
              {stationSearch && (
                <button onClick={() => setStationSearch('')} className="sidebar-search__clear">
                  <X size={12} />
                </button>
              )}
            </div>

            {/* Filtro por río — combobox con dropdown */}
            <div className="sidebar-search__inner" ref={riverComboboxRef} style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Filtrar por río…"
                value={riverInput}
                onChange={(e) => {
                  setRiverInput(e.target.value);
                  setRiverFilter('');
                  setRiverDropdownOpen(true);
                }}
                onFocus={() => setRiverDropdownOpen(true)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape' || e.key === 'Enter') setRiverDropdownOpen(false);
                }}
                className="sidebar-search__input sidebar-search__input--river"
                autoComplete="off"
              />
              {riverInput && (
                <button onClick={handleClearRiver} className="sidebar-search__clear sidebar-search__clear--river">
                  <X size={12} />
                </button>
              )}
              {riverDropdownOpen && dropdownRivers.length > 0 && (
                <ul className="river-dropdown">
                  {dropdownRivers.map((river) => (
                    <li
                      key={river}
                      className={`river-dropdown__item${riverFilter === river ? ' river-dropdown__item--active' : ''}`}
                      onMouseDown={() => handleSelectRiver(river)}
                    >
                      {river}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="station-list" ref={listRef}>
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
                      ref={(el) => {
                        if (el) itemRefs.current.set(station.id, el);
                        else itemRefs.current.delete(station.id);
                      }}
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

      <SourcesFooter />
    </>
  );
}

export default App;

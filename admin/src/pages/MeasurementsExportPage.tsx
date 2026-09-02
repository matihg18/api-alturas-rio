import { useEffect, useState, useRef, useMemo } from 'react';
import { Download, FileDown, CalendarRange, X } from 'lucide-react';
import { api } from '../services/adminApi';
import type { Station } from '../services/adminApi';
import { useToast } from '../components/Toast';

export function MeasurementsExportPage() {
  const { show } = useToast();
  const [stations, setStations] = useState<Station[]>([]);
  const [loadingStations, setLoadingStations] = useState(true);

  // Combobox de estación
  const [stationInput, setStationInput] = useState<string>('');
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const comboboxRef = useRef<HTMLDivElement>(null);

  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate]     = useState<string>('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    api.stations.list()
      .then(setStations)
      .catch(() => show('Error al cargar las estaciones', 'error'))
      .finally(() => setLoadingStations(false));
  }, []);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (comboboxRef.current && !comboboxRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filtrar estaciones según lo que se escribe
  const filteredStations = useMemo(() => {
    const q = stationInput.trim().toLowerCase();
    if (!q) return stations;
    return stations.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.river.toLowerCase().includes(q) ||
        s.source.toLowerCase().includes(q),
    );
  }, [stations, stationInput]);

  const handleSelectStation = (s: Station) => {
    setSelectedStation(s);
    setStationInput(s.name);
    setDropdownOpen(false);
  };

  const handleClearStation = () => {
    setSelectedStation(null);
    setStationInput('');
    setDropdownOpen(false);
  };

  const handleDownload = async () => {
    if (!selectedStation) { show('Seleccioná una estación', 'error'); return; }
    if (!fromDate)         { show('Ingresá una fecha de inicio', 'error'); return; }
    if (!toDate)           { show('Ingresá una fecha de fin', 'error'); return; }
    if (fromDate > toDate) { show('La fecha de inicio no puede ser posterior a la de fin', 'error'); return; }

    setDownloading(true);
    try {
      const { blob, filename } = await api.measurements.exportCsv(
        selectedStation.id,
        fromDate,
        toDate,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      show('CSV descargado correctamente');
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al descargar el CSV', 'error');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="page-header__left">
          <h1 className="page-title">Exportar mediciones</h1>
          <p className="page-subtitle">
            Seleccioná una estación y un rango de fechas para descargar las mediciones en formato CSV.
          </p>
        </div>
      </div>

      <div className="page-body">
        <div className="card" style={{ maxWidth: '560px', padding: '2rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

            {/* Banner informativo */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.875rem',
              padding: '1.125rem 1.375rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent-muted)',
              border: '1px solid var(--accent-border)',
            }}>
              <FileDown size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                El archivo descargado contendrá dos columnas:{' '}
                <strong style={{ color: 'var(--text-primary)' }}>date_time</strong> y{' '}
                <strong style={{ color: 'var(--text-primary)' }}>value</strong>, ordenadas cronológicamente.
              </span>
            </div>

            {/* Combobox de estación */}
            <div className="form-group">
              <label className="form-label" htmlFor="export-station">Estación</label>

              {loadingStations ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                  <span className="spinner" style={{ width: 14, height: 14 }} />
                  Cargando estaciones…
                </div>
              ) : (
                <div className="river-combobox" ref={comboboxRef} style={{ width: '100%' }}>
                  <input
                    id="export-station"
                    type="text"
                    className="form-input"
                    placeholder="Buscar por nombre, río o fuente…"
                    value={stationInput}
                    autoComplete="off"
                    onChange={(e) => {
                      setStationInput(e.target.value);
                      setSelectedStation(null);
                      setDropdownOpen(true);
                    }}
                    onFocus={() => setDropdownOpen(true)}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') setDropdownOpen(false);
                      if (e.key === 'Enter' && filteredStations.length === 1) {
                        handleSelectStation(filteredStations[0]);
                      }
                    }}
                  />

                  {stationInput && (
                    <button
                      className="river-combobox__clear"
                      onClick={handleClearStation}
                      title="Limpiar selección"
                    >
                      <X size={12} />
                    </button>
                  )}

                  {dropdownOpen && filteredStations.length > 0 && (
                    <ul className="river-dropdown">
                      {filteredStations.map((s) => (
                        <li
                          key={s.id}
                          className={`river-dropdown__item${selectedStation?.id === s.id ? ' river-dropdown__item--active' : ''}`}
                          onMouseDown={() => handleSelectStation(s)}
                        >
                          <span style={{ fontWeight: 500 }}>{s.name}</span>
                          <span style={{ color: 'var(--text-muted)', marginLeft: '0.4rem', fontSize: '0.78rem' }}>
                            · {s.river} · {s.source}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}

                  {dropdownOpen && stationInput.trim() && filteredStations.length === 0 && (
                    <ul className="river-dropdown">
                      <li style={{ padding: '0.5rem 0.75rem', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                        Sin resultados para "{stationInput}"
                      </li>
                    </ul>
                  )}
                </div>
              )}

              {selectedStation && (
                <span className="form-hint">
                  Fuente: <strong>{selectedStation.source}</strong>
                  {selectedStation.gauge_point ? ` · Punto de aforo: ${selectedStation.gauge_point.name}` : ''}
                </span>
              )}
            </div>

            {/* Rango de fechas */}
            <div style={{ display: 'flex', gap: '1rem' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label" htmlFor="export-from">
                  <CalendarRange size={13} style={{ display: 'inline', marginRight: '0.3rem', verticalAlign: 'middle' }} />
                  Desde
                </label>
                <input
                  id="export-from"
                  type="date"
                  className="form-input"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label className="form-label" htmlFor="export-to">
                  <CalendarRange size={13} style={{ display: 'inline', marginRight: '0.3rem', verticalAlign: 'middle' }} />
                  Hasta
                </label>
                <input
                  id="export-to"
                  type="date"
                  className="form-input"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                />
              </div>
            </div>

            {/* Botón */}
            <button
              id="export-download-btn"
              className="btn btn-primary"
              onClick={handleDownload}
              disabled={downloading || loadingStations}
              style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              {downloading
                ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Descargando…</>
                : <><Download size={15} /> Descargar CSV</>
              }
            </button>

          </div>
        </div>
      </div>
    </>
  );
}

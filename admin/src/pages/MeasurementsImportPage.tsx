import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import { Upload, FileUp, X, CheckCircle, AlertCircle, SkipForward } from 'lucide-react';
import { api } from '../services/adminApi';
import type { Station, MeasurementImportResult } from '../services/adminApi';
import { useToast } from '../components/Toast';

export function MeasurementsImportPage() {
  const { show } = useToast();
  const [stations, setStations] = useState<Station[]>([]);
  const [loadingStations, setLoadingStations] = useState(true);

  // Combobox de estación
  const [stationInput, setStationInput] = useState<string>('');
  const [selectedStation, setSelectedStation] = useState<Station | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const comboboxRef = useRef<HTMLDivElement>(null);

  // Archivo
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Estado de la importación
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<MeasurementImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

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

  const acceptFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith('.csv')) {
      show('El archivo debe tener extensión .csv', 'error');
      return;
    }
    setFile(f);
    setResult(null);
    setImportError(null);
  }, [show]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) acceptFile(dropped);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0];
    if (picked) acceptFile(picked);
    // Resetear el input para que el mismo archivo pueda volver a elegirse
    e.target.value = '';
  };

  const handleImport = async () => {
    if (!selectedStation) { show('Seleccioná una estación', 'error'); return; }
    if (!file)            { show('Seleccioná un archivo CSV', 'error'); return; }

    setImporting(true);
    setResult(null);
    setImportError(null);
    try {
      const res = await api.measurements.importCsv(selectedStation.id, file);
      setResult(res);
      if (res.inserted > 0) {
        show(`Importación exitosa: ${res.inserted} medición(es) insertada(s)`);
      } else {
        show('Importación completada — no se insertaron mediciones nuevas', 'error');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al importar el CSV';
      setImportError(msg);
      show('El CSV contiene errores — no se insertó ninguna medición', 'error');
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="page-header__left">
          <h1 className="page-title">Importar mediciones</h1>
          <p className="page-subtitle">
            Cargá un CSV con mediciones históricas. Las mediciones ya existentes en la base de datos tienen preponderancia y no se sobreescriben.
          </p>
        </div>
      </div>

      <div className="page-body">
        <div className="card" style={{ maxWidth: '580px', padding: '2rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

            {/* Banner de formato */}
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.875rem',
              padding: '1.125rem 1.375rem',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent-muted)',
              border: '1px solid var(--accent-border)',
            }}>
              <FileUp size={20} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: '0.1rem' }} />
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <div>El CSV debe tener <strong style={{ color: 'var(--text-primary)' }}>exactamente</strong> esta cabecera:</div>
                <code style={{
                  display: 'inline-block',
                  marginTop: '0.35rem',
                  padding: '0.25rem 0.6rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(0,0,0,0.3)',
                  color: 'var(--accent-hover)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  letterSpacing: '0.02em',
                }}>date_time,value</code>
                <div style={{ marginTop: '0.4rem' }}>
                  Fechas en formato <code style={{ color: 'var(--accent-hover)', fontFamily: 'var(--font-mono)' }}>YYYY-MM-DDTHH:MM:SS</code> · valores decimales con punto.
                </div>
              </div>
            </div>

            {/* Combobox de estación */}
            <div className="form-group">
              <label className="form-label" htmlFor="import-station">Estación destino</label>
              {loadingStations ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                  <span className="spinner" style={{ width: 14, height: 14 }} />
                  Cargando estaciones…
                </div>
              ) : (
                <div className="river-combobox" ref={comboboxRef} style={{ width: '100%' }}>
                  <input
                    id="import-station"
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
                    <button className="river-combobox__clear" onClick={handleClearStation} title="Limpiar">
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

            {/* Zona de drag & drop */}
            <div className="form-group">
              <label className="form-label">Archivo CSV</label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${dragging ? 'var(--accent)' : file ? 'var(--success)' : 'var(--border-strong)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '2rem 1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.5rem',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s, background 0.2s',
                  background: dragging
                    ? 'var(--accent-muted)'
                    : file
                    ? 'var(--success-muted)'
                    : 'transparent',
                  userSelect: 'none',
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                <Upload
                  size={24}
                  style={{ color: file ? 'var(--success)' : 'var(--text-muted)', transition: 'color 0.2s' }}
                />
                {file ? (
                  <>
                    <span style={{ fontWeight: 600, color: 'var(--success)', fontSize: '0.875rem' }}>
                      {file.name}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {(file.size / 1024).toFixed(1)} KB · Clic para cambiar
                    </span>
                  </>
                ) : (
                  <>
                    <span style={{ fontWeight: 500, color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                      Arrastrá el CSV aquí o hacé clic para seleccionar
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      Solo se aceptan archivos .csv
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Botón */}
            <button
              id="import-submit-btn"
              className="btn btn-primary"
              onClick={handleImport}
              disabled={importing || loadingStations}
              style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              {importing
                ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Importando…</>
                : <><Upload size={15} /> Importar CSV</>
              }
            </button>

            {/* Resultado exitoso */}
            {result && (
              <div style={{
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: '0.75rem 1.25rem',
                  background: 'color-mix(in srgb, var(--success) 10%, transparent)',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  color: 'var(--success)',
                }}>
                  <CheckCircle size={16} />
                  Importación completada
                </div>
                <div style={{ display: 'flex', padding: '1.25rem', gap: '1.5rem' }}>
                  {[
                    { label: 'Total en CSV', value: result.total,    color: 'var(--text-primary)' },
                    { label: 'Insertadas',   value: result.inserted, color: 'var(--text-primary)' },
                    { label: 'Omitidas',     value: result.skipped,  color: 'var(--text-primary)' },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ textAlign: 'center', flex: 1 }}>
                      <div style={{ fontSize: '1.6rem', fontWeight: 700, color, lineHeight: 1.1 }}>
                        {value}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        {label}
                      </div>
                    </div>
                  ))}
                </div>
                {result.skipped > 0 && (
                  <div style={{
                    padding: '0.6rem 1.25rem',
                    borderTop: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)',
                  }}>
                    <SkipForward size={13} />
                    Las mediciones omitidas ya existían para esa estación y fueron preservadas.
                  </div>
                )}
              </div>
            )}

            {/* Error de validación */}
            {importError && (
              <div style={{
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--danger-border)',
                overflow: 'hidden',
              }}>
                <div style={{
                  padding: '0.75rem 1.25rem',
                  background: 'var(--danger-muted)',
                  borderBottom: '1px solid var(--danger-border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  color: 'var(--danger)',
                }}>
                  <AlertCircle size={16} />
                  No se insertó ninguna medición
                </div>
                <pre style={{
                  padding: '1rem 1.25rem',
                  margin: 0,
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'var(--font-mono)',
                  lineHeight: 1.6,
                  background: 'transparent',
                }}>
                  {importError}
                </pre>
              </div>
            )}

          </div>
        </div>
      </div>
    </>
  );
}

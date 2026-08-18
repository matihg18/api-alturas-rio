import { useEffect, useState, useRef, useMemo } from 'react';
import { Layers, Link2, Link2Off, MapPin, Pencil, X } from 'lucide-react';
import { api } from '../services/adminApi';
import type { Station, GaugePoint, StationCoordinatesUpdate } from '../services/adminApi';

import { Modal } from '../components/Modal';
import { useToast } from '../components/Toast';

export function StationsPage() {
  const { show } = useToast();
  const [stations, setStations] = useState<Station[]>([]);
  const [gaugePoints, setGaugePoints] = useState<GaugePoint[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal: asignar punto de aforo
  const [editStation, setEditStation] = useState<Station | null>(null);
  const [selectedGpId, setSelectedGpId] = useState<string>('');
  const [saving, setSaving] = useState(false);

  // Modal: editar coordenadas
  const [coordStation, setCoordStation] = useState<Station | null>(null);
  const [coordLat, setCoordLat] = useState<string>('');
  const [coordLng, setCoordLng] = useState<string>('');
  const [savingCoords, setSavingCoords] = useState(false);

  const [stationSearch, setStationSearch] = useState('');
  const [riverFilter, setRiverFilter] = useState('');
  const [riverInput, setRiverInput] = useState('');
  const [riverDropdownOpen, setRiverDropdownOpen] = useState(false);
  const riverComboboxRef = useRef<HTMLDivElement>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [s, gp] = await Promise.all([api.stations.list(), api.gaugePoints.list()]);
      setStations(s);
      setGaugePoints(gp);
    } catch { show('Error al cargar datos', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  // ── Punto de aforo ────────────────────────────────────────────────────────

  const openEdit = (s: Station) => {
    setEditStation(s);
    setSelectedGpId(s.gauge_point_id?.toString() ?? '');
  };

  const handleSave = async () => {
    if (!editStation) return;
    setSaving(true);
    try {
      await api.stations.assignGaugePoint(editStation.id, {
        gauge_point_id: selectedGpId ? parseInt(selectedGpId) : null,
      });
      show('Punto de aforo actualizado');
      setEditStation(null);
      load();
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al guardar', 'error');
    } finally { setSaving(false); }
  };

  // ── Visibilidad ───────────────────────────────────────────────────────────

  const handleToggleVisibility = async (station: Station) => {
    const newValue = !station.is_visible;
    setStations((prev) =>
      prev.map((s) => s.id === station.id ? { ...s, is_visible: newValue } : s)
    );
    setTogglingId(station.id);
    try {
      await api.stations.toggleVisibility(station.id, newValue);
      show(newValue ? `"${station.name}" habilitada en el dashboard` : `"${station.name}" ocultada del dashboard`);
    } catch (e: unknown) {
      setStations((prev) =>
        prev.map((s) => s.id === station.id ? { ...s, is_visible: !newValue } : s)
      );
      show(e instanceof Error ? e.message : 'Error al cambiar visibilidad', 'error');
    } finally {
      setTogglingId(null);
    }
  };

  // ── Coordenadas ───────────────────────────────────────────────────────────

  const openCoords = (s: Station) => {
    setCoordStation(s);
    setCoordLat(s.latitud !== null ? String(s.latitud) : '');
    setCoordLng(s.longitud !== null ? String(s.longitud) : '');
  };

  const handleSaveCoords = async () => {
    if (!coordStation) return;
    setSavingCoords(true);

    const parsedLat = coordLat.trim() !== '' ? parseFloat(coordLat) : null;
    const parsedLng = coordLng.trim() !== '' ? parseFloat(coordLng) : null;

    if (parsedLat !== null && (parsedLat < -90 || parsedLat > 90)) {
      show('La latitud debe estar entre -90 y 90', 'error');
      setSavingCoords(false);
      return;
    }
    if (parsedLng !== null && (parsedLng < -180 || parsedLng > 180)) {
      show('La longitud debe estar entre -180 y 180', 'error');
      setSavingCoords(false);
      return;
    }

    const body: StationCoordinatesUpdate = { latitud: parsedLat, longitud: parsedLng };

    // Optimistic update
    setStations((prev) =>
      prev.map((s) => s.id === coordStation.id ? { ...s, ...body } : s)
    );

    try {
      await api.stations.updateCoordinates(coordStation.id, body);
      show(`Coordenadas de "${coordStation.name}" actualizadas`);
      setCoordStation(null);
    } catch (e: unknown) {
      // Revertir si falla
      setStations((prev) =>
        prev.map((s) =>
          s.id === coordStation.id
            ? { ...s, latitud: coordStation.latitud, longitud: coordStation.longitud }
            : s
        )
      );
      show(e instanceof Error ? e.message : 'Error al guardar coordenadas', 'error');
    } finally {
      setSavingCoords(false);
    }
  };

  // ── Filtrado ──────────────────────────────────────────────────────────────

  const uniqueRivers = useMemo(() => {
    const set = new Set(stations.map((s) => s.river));
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'es'));
  }, [stations]);

  const dropdownRivers = useMemo(() => {
    if (!riverInput.trim()) return uniqueRivers;
    const q = riverInput.toLowerCase();
    const prefix = uniqueRivers.filter((r) => r.toLowerCase().startsWith(q));
    const internal = uniqueRivers.filter(
      (r) => !r.toLowerCase().startsWith(q) && r.toLowerCase().includes(q)
    );
    return [...prefix, ...internal];
  }, [uniqueRivers, riverInput]);

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

  const filtered = stations.filter((s) => {
    const matchName = s.name.toLowerCase().includes(stationSearch.toLowerCase()) ||
      s.source.toLowerCase().includes(stationSearch.toLowerCase());
    const matchRiver = riverInput.trim() === '' ||
      s.river.toLowerCase().includes(riverInput.toLowerCase());
    return matchName && matchRiver;
  });

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <div className="page-header">
        <div className="page-header__left">
          <h1 className="page-title">Estaciones</h1>
          <p className="page-subtitle">
            Listado de estaciones hidrológicas. Podés asignar el punto de aforo, editar coordenadas y controlar la visibilidad en el dashboard.
          </p>
        </div>
        <div className="page-header__filters">
          {/* Filtro por nombre / fuente */}
          <input
            id="station-search"
            type="text"
            className="form-input"
            placeholder="Buscar por nombre o fuente…"
            value={stationSearch}
            onChange={(e) => setStationSearch(e.target.value)}
          />
          {/* Filtro por río — combobox */}
          <div className="river-combobox" ref={riverComboboxRef}>
            <input
              id="river-search"
              type="text"
              className="form-input"
              placeholder="Filtrar por río…"
              value={riverInput}
              autoComplete="off"
              onChange={(e) => {
                setRiverInput(e.target.value);
                setRiverFilter('');
                setRiverDropdownOpen(true);
              }}
              onFocus={() => setRiverDropdownOpen(true)}
              onKeyDown={(e) => {
                if (e.key === 'Escape' || e.key === 'Enter') setRiverDropdownOpen(false);
              }}
            />
            {riverInput && (
              <button className="river-combobox__clear" onClick={handleClearRiver} title="Limpiar filtro de río">
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
      </div>

      <div className="page-body">
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nombre</th>
                  <th>Río</th>
                  <th>Fuente</th>
                  <th>Punto de aforo</th>
                  <th>Coordenadas</th>
                  <th style={{ textAlign: 'center' }}>Visible en frontend</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row">
                    <td colSpan={7}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                        <span className="spinner" /> Cargando estaciones…
                      </div>
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      <div className="empty-state">
                        <Layers size={28} className="empty-state__icon" />
                        <div className="empty-state__title">No hay estaciones</div>
                        <div className="empty-state__desc">Las estaciones son creadas por el scraper automáticamente.</div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filtered.map((s) => (
                    <tr key={s.id} className={!s.is_visible ? 'station-row--hidden' : ''}>
                      <td className="td-mono">#{s.id}</td>
                      <td className="td-primary">{s.name}</td>
                      <td>{s.river}</td>
                      <td><span className="badge badge-muted">{s.source}</span></td>
                      <td
                        id={`assign-gp-${s.id}`}
                        className="td-editable"
                        onClick={() => openEdit(s)}
                        title="Clic para cambiar el punto de aforo"
                      >
                        <span className="td-editable__content">
                          {s.gauge_point ? (
                            <span className="badge badge-accent">
                              <Link2 size={10} /> {s.gauge_point.name}
                            </span>
                          ) : (
                            <span className="badge badge-muted">
                              <Link2Off size={10} /> Sin asignar
                            </span>
                          )}
                          <span className="td-editable__hint"><Pencil size={11} /></span>
                        </span>
                      </td>
                      <td
                        id={`edit-coords-${s.id}`}
                        className="td-editable"
                        onClick={() => openCoords(s)}
                        title="Clic para editar las coordenadas"
                      >
                        <span className="td-editable__content">
                          {s.latitud !== null && s.longitud !== null ? (
                            <span className="badge badge-accent">
                              <MapPin size={10} />
                              {s.latitud.toFixed(4)}, {s.longitud.toFixed(4)}
                            </span>
                          ) : (
                            <span className="badge badge-warning">
                              <MapPin size={10} /> Sin coordenadas
                            </span>
                          )}
                          <span className="td-editable__hint"><Pencil size={11} /></span>
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <label
                          className="toggle-switch"
                          title={s.is_visible ? 'Ocultar del frontend' : 'Mostrar en el frontend'}
                        >
                          <input
                            id={`visibility-toggle-${s.id}`}
                            type="checkbox"
                            checked={s.is_visible}
                            disabled={togglingId === s.id}
                            onChange={() => handleToggleVisibility(s)}
                          />
                          <span className="toggle-switch__track">
                            <span className="toggle-switch__thumb" />
                          </span>
                        </label>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal: asignar punto de aforo */}
      {editStation && (
        <Modal
          title={`Asignar punto de aforo — ${editStation.name}`}
          onClose={() => setEditStation(null)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setEditStation(null)} disabled={saving}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? <span className="spinner" style={{ width: 14, height: 14 }} /> : null}
                Guardar
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label" htmlFor="gp-select">Punto de aforo</label>
            <select
              id="gp-select"
              className="form-select"
              value={selectedGpId}
              onChange={(e) => setSelectedGpId(e.target.value)}
            >
              <option value="">— Sin asignar —</option>
              {gaugePoints.map((gp) => (
                <option key={gp.id} value={gp.id}>{gp.name}{gp.river ? ` · ${gp.river}` : ''}</option>
              ))}
            </select>
            <span className="form-hint">Seleccionar "Sin asignar" desvincula el punto de aforo actual.</span>
          </div>
        </Modal>
      )}

      {/* Modal: editar coordenadas */}
      {coordStation && (
        <Modal
          title={`Editar coordenadas — ${coordStation.name}`}
          onClose={() => setCoordStation(null)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setCoordStation(null)} disabled={savingCoords}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleSaveCoords} disabled={savingCoords}>
                {savingCoords ? <span className="spinner" style={{ width: 14, height: 14 }} /> : null}
                Guardar
              </button>
            </>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                background: coordStation.latitud !== null && coordStation.longitud !== null
                  ? 'color-mix(in srgb, var(--color-accent) 12%, transparent)'
                  : 'color-mix(in srgb, #f59e0b 12%, transparent)',
                fontSize: '0.8125rem',
                color: coordStation.latitud !== null && coordStation.longitud !== null
                  ? 'var(--color-accent)'
                  : '#f59e0b',
              }}
            >
              <MapPin size={14} />
              {coordStation.latitud !== null && coordStation.longitud !== null
                ? `Coordenadas actuales: ${coordStation.latitud}, ${coordStation.longitud}`
                : 'Esta estación no tiene coordenadas definidas'}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="coord-lat">Latitud</label>
              <input
                id="coord-lat"
                type="number"
                className="form-input"
                placeholder="Ej: -34.6037"
                step="any"
                min="-90"
                max="90"
                value={coordLat}
                onChange={(e) => setCoordLat(e.target.value)}
              />
              <span className="form-hint">Valor entre -90 y 90. Dejarlo vacío para eliminar.</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="coord-lng">Longitud</label>
              <input
                id="coord-lng"
                type="number"
                className="form-input"
                placeholder="Ej: -58.3816"
                step="any"
                min="-180"
                max="180"
                value={coordLng}
                onChange={(e) => setCoordLng(e.target.value)}
              />
              <span className="form-hint">Valor entre -180 y 180. Dejarlo vacío para eliminar.</span>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}


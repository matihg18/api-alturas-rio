import { useEffect, useState } from 'react';
import { Layers, Link2, Link2Off } from 'lucide-react';
import { api } from '../services/adminApi';
import type { Station, GaugePoint } from '../services/adminApi';

import { Modal } from '../components/Modal';
import { useToast } from '../components/Toast';

export function StationsPage() {
  const { show } = useToast();
  const [stations, setStations] = useState<Station[]>([]);
  const [gaugePoints, setGaugePoints] = useState<GaugePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [editStation, setEditStation] = useState<Station | null>(null);
  const [selectedGpId, setSelectedGpId] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');
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

  const filtered = stations.filter(
    (s) => s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.river.toLowerCase().includes(search.toLowerCase()) ||
      s.source.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="page-header">
        <div className="page-header__left">
          <h1 className="page-title">Estaciones</h1>
          <p className="page-subtitle">
            Listado de estaciones hidrológicas. Podés asignar el punto de aforo y controlar la visibilidad en el dashboard.
          </p>
        </div>
        <input
          id="station-search"
          type="text"
          className="form-input"
          placeholder="Filtrar por nombre, río o fuente…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 260 }}
        />
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
                  <th style={{ textAlign: 'center' }}>Visible en frontend</th>
                  <th style={{ textAlign: 'right' }}>Acciones</th>
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
                      <td>
                        {s.gauge_point ? (
                          <span className="badge badge-accent">
                            <Link2 size={10} /> {s.gauge_point.name}
                          </span>
                        ) : (
                          <span className="badge badge-muted">
                            <Link2Off size={10} /> Sin asignar
                          </span>
                        )}
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
                      <td>
                        <div className="td-actions">
                          <button id={`assign-gp-${s.id}`} className="btn btn-secondary btn-sm" onClick={() => openEdit(s)}>
                            Asignar punto de aforo
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

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
    </>
  );
}

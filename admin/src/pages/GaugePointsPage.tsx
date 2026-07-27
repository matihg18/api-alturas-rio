import { useEffect, useState } from 'react';
import { MapPin, Plus, Pencil, Trash2 } from 'lucide-react';
import { api } from '../services/adminApi';
import type { GaugePoint, GaugePointCreate, GaugePointUpdate } from '../services/adminApi';

import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';

type FormData = { name: string; river: string; description: string };
const emptyForm = (): FormData => ({ name: '', river: '', description: '' });

export function GaugePointsPage() {
  const { show } = useToast();
  const [items, setItems] = useState<GaugePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<GaugePoint | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<GaugePoint | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<FormData>>({});

  const load = async () => {
    setLoading(true);
    try { setItems(await api.gaugePoints.list()); }
    catch { show('Error al cargar puntos de aforo', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); setForm(emptyForm()); setErrors({}); setModalOpen(true); };
  const openEdit = (gp: GaugePoint) => {
    setEditing(gp);
    setForm({ name: gp.name, river: gp.river ?? '', description: gp.description ?? '' });
    setErrors({});
    setModalOpen(true);
  };

  const validate = (): boolean => {
    const e: Partial<FormData> = {};
    if (!form.name.trim()) e.name = 'El nombre es obligatorio';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      if (editing) {
        const body: GaugePointUpdate = {
          name: form.name.trim() || undefined,
          river: form.river.trim() || undefined,
          description: form.description.trim() || undefined,
        };
        await api.gaugePoints.update(editing.id, body);
        show('Punto de aforo actualizado');
      } else {
        const body: GaugePointCreate = {
          name: form.name.trim(),
          river: form.river.trim() || undefined,
          description: form.description.trim() || undefined,
        };
        await api.gaugePoints.create(body);
        show('Punto de aforo creado');
      }
      setModalOpen(false);
      load();
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al guardar', 'error');
    } finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await api.gaugePoints.delete(deleting.id);
      show('Punto de aforo eliminado');
      setDeleting(null);
      load();
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al eliminar', 'error');
    } finally { setDeleteLoading(false); }
  };

  const field = (key: keyof FormData) => ({
    value: form[key],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

  return (
    <>
      <div className="page-header">
        <div className="page-header__left">
          <h1 className="page-title">Puntos de aforo</h1>
          <p className="page-subtitle">Puntos de aforo asociados a estaciones. Gestionados manualmente.</p>
        </div>
        <button id="create-gauge-point" className="btn btn-primary" onClick={openCreate}>
          <Plus size={15} /> Nuevo punto de aforo
        </button>
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
                  <th>Descripción</th>
                  <th style={{ textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row"><td colSpan={5}><div style={{ display:'flex',alignItems:'center',justifyContent:'center',gap:'0.5rem' }}><span className="spinner"/>Cargando…</div></td></tr>
                ) : items.length === 0 ? (
                  <tr><td colSpan={5}><div className="empty-state"><MapPin size={28} className="empty-state__icon"/><div className="empty-state__title">Sin puntos de aforo</div><div className="empty-state__desc">Creá el primero con el botón de arriba.</div></div></td></tr>
                ) : items.map((gp) => (
                  <tr key={gp.id}>
                    <td className="td-mono">#{gp.id}</td>
                    <td className="td-primary">{gp.name}</td>
                    <td>{gp.river ?? <span className="text-muted">—</span>}</td>
                    <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {gp.description ?? <span className="text-muted">—</span>}
                    </td>
                    <td>
                      <div className="td-actions">
                        <button id={`edit-gp-${gp.id}`} className="btn btn-ghost btn-sm" onClick={() => openEdit(gp)} title="Editar"><Pencil size={13}/></button>
                        <button id={`delete-gp-${gp.id}`} className="btn btn-ghost btn-sm" onClick={() => setDeleting(gp)} title="Eliminar" style={{ color: 'var(--danger)' }}><Trash2 size={13}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {modalOpen && (
        <Modal
          title={editing ? `Editar: ${editing.name}` : 'Nuevo punto de aforo'}
          onClose={() => setModalOpen(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setModalOpen(false)} disabled={saving}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? <span className="spinner" style={{ width:14,height:14 }}/> : null}
                {editing ? 'Guardar cambios' : 'Crear'}
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label" htmlFor="gp-name">Nombre <span className="req">*</span></label>
            <input id="gp-name" className="form-input" placeholder="Ej: Concordia" {...field('name')} />
            {errors.name && <span className="text-danger">{errors.name}</span>}
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="gp-river">Río</label>
            <input id="gp-river" className="form-input" placeholder="Ej: Uruguay" {...field('river')} />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="gp-desc">Descripción</label>
            <textarea id="gp-desc" className="form-textarea" placeholder="Descripción opcional…" {...field('description')} />
          </div>
        </Modal>
      )}

      {deleting && (
        <ConfirmDialog
          title="Eliminar punto de aforo"
          onConfirm={handleDelete}
          onCancel={() => setDeleting(null)}
          loading={deleteLoading}
        >
          ¿Eliminar el punto de aforo <span className="confirm-entity">"{deleting.name}"</span>?{' '}
          Esta acción también desvinculará todas las estaciones asociadas y eliminará sus correcciones.
        </ConfirmDialog>
      )}
    </>
  );
}

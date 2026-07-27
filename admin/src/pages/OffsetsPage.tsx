import { useEffect, useState } from 'react';
import { Sliders, Plus, Pencil, Trash2 } from 'lucide-react';
import { api } from '../services/adminApi';
import type { Offset, GaugePoint, DatumType, OffsetCreate, OffsetUpdate } from '../services/adminApi';

import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';

type CreateForm = { gauge_point_id: string; datum_type_id: string; offset_local_to_datum: string };
type UpdateForm = { offset_local_to_datum: string };
const emptyCreate = (): CreateForm => ({ gauge_point_id: '', datum_type_id: '', offset_local_to_datum: '' });

export function OffsetsPage() {
  const { show } = useToast();
  const [items, setItems] = useState<Offset[]>([]);
  const [gaugePoints, setGaugePoints] = useState<GaugePoint[]>([]);
  const [datumTypes, setDatumTypes] = useState<DatumType[]>([]);
  const [loading, setLoading] = useState(true);

  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateForm>(emptyCreate());
  const [createErrors, setCreateErrors] = useState<Partial<CreateForm>>({});
  const [creating, setCreating] = useState(false);

  const [editing, setEditing] = useState<Offset | null>(null);
  const [updateForm, setUpdateForm] = useState<UpdateForm>({ offset_local_to_datum: '' });
  const [updateError, setUpdateError] = useState('');
  const [updating, setUpdating] = useState(false);

  const [deleting, setDeleting] = useState<Offset | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [filterGp, setFilterGp] = useState<string>('');

  const load = async () => {
    setLoading(true);
    try {
      const [o, gp, dt] = await Promise.all([
        api.offsets.list(filterGp ? parseInt(filterGp) : undefined),
        api.gaugePoints.list(),
        api.datumTypes.list(),
      ]);
      setItems(o);
      setGaugePoints(gp);
      setDatumTypes(dt);
    } catch { show('Error al cargar correcciones', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filterGp]);

  const validateCreate = (): boolean => {
    const e: Partial<CreateForm> = {};
    if (!createForm.gauge_point_id) e.gauge_point_id = 'Requerido';
    if (!createForm.datum_type_id) e.datum_type_id = 'Requerido';
    if (!createForm.offset_local_to_datum || isNaN(Number(createForm.offset_local_to_datum)))
      e.offset_local_to_datum = 'Debe ser un número válido';
    setCreateErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleCreate = async () => {
    if (!validateCreate()) return;
    setCreating(true);
    try {
      const body: OffsetCreate = {
        gauge_point_id: parseInt(createForm.gauge_point_id),
        datum_type_id: parseInt(createForm.datum_type_id),
        offset_local_to_datum: parseFloat(createForm.offset_local_to_datum),
      };
      await api.offsets.create(body);
      show('Corrección creada');
      setCreateOpen(false);
      setCreateForm(emptyCreate());
      load();
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al crear', 'error');
    } finally { setCreating(false); }
  };

  const openEdit = (o: Offset) => {
    setEditing(o);
    setUpdateForm({ offset_local_to_datum: o.offset_local_to_datum.toString() });
    setUpdateError('');
  };

  const handleUpdate = async () => {
    if (!editing) return;
    if (!updateForm.offset_local_to_datum || isNaN(Number(updateForm.offset_local_to_datum))) {
      setUpdateError('Debe ser un número válido');
      return;
    }
    setUpdating(true);
    try {
      const body: OffsetUpdate = { offset_local_to_datum: parseFloat(updateForm.offset_local_to_datum) };
      await api.offsets.update(editing.id, body);
      show('Corrección actualizada');
      setEditing(null);
      load();
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al actualizar', 'error');
    } finally { setUpdating(false); }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await api.offsets.delete(deleting.id);
      show('Corrección eliminada');
      setDeleting(null);
      load();
    } catch (e: unknown) {
      show(e instanceof Error ? e.message : 'Error al eliminar', 'error');
    } finally { setDeleteLoading(false); }
  };

  return (
    <>
      <div className="page-header">
        <div className="page-header__left">
          <h1 className="page-title">Correcciones de cero</h1>
          <p className="page-subtitle">
            Corrección entre el cero local de un punto de aforo y un datum de referencia.
          </p>
        </div>
        <div style={{ display:'flex',gap:'0.5rem',alignItems:'center' }}>
          <select
            id="filter-gauge-point"
            className="form-select"
            value={filterGp}
            onChange={(e) => setFilterGp(e.target.value)}
            style={{ minWidth: 180 }}
          >
            <option value="">Todos los puntos de aforo</option>
            {gaugePoints.map((gp) => (
              <option key={gp.id} value={gp.id}>{gp.name}</option>
            ))}
          </select>
          <button id="create-offset" className="btn btn-primary" onClick={() => { setCreateForm(emptyCreate()); setCreateErrors({}); setCreateOpen(true); }}>
            <Plus size={15}/> Nueva corrección
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Punto de aforo</th>
                  <th>Datum</th>
                  <th>Corrección (local → datum)</th>
                  <th style={{ textAlign:'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row"><td colSpan={5}><div style={{ display:'flex',alignItems:'center',justifyContent:'center',gap:'0.5rem' }}><span className="spinner"/>Cargando…</div></td></tr>
                ) : items.length === 0 ? (
                  <tr><td colSpan={5}><div className="empty-state"><Sliders size={28} className="empty-state__icon"/><div className="empty-state__title">Sin correcciones</div><div className="empty-state__desc">Creá la primera con el botón de arriba.</div></div></td></tr>
                ) : items.map((o) => (
                  <tr key={o.id}>
                    <td className="td-mono">#{o.id}</td>
                    <td className="td-primary">{o.gauge_point.name}{o.gauge_point.river ? ` · ${o.gauge_point.river}` : ''}</td>
                    <td><span className="badge badge-code">{o.datum_type.code}</span></td>
                    <td className="td-mono" style={{ color: o.offset_local_to_datum >= 0 ? 'var(--success)' : 'var(--warning)' }}>
                      {o.offset_local_to_datum >= 0 ? '+' : ''}{o.offset_local_to_datum} m
                    </td>
                    <td>
                      <div className="td-actions">
                        <button id={`edit-offset-${o.id}`} className="btn btn-ghost btn-sm" onClick={() => openEdit(o)} title="Editar"><Pencil size={13}/></button>
                        <button id={`delete-offset-${o.id}`} className="btn btn-ghost btn-sm" onClick={() => setDeleting(o)} title="Eliminar" style={{ color:'var(--danger)' }}><Trash2 size={13}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal crear */}
      {createOpen && (
        <Modal
          title="Nueva corrección"
          onClose={() => setCreateOpen(false)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setCreateOpen(false)} disabled={creating}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
                {creating ? <span className="spinner" style={{ width:14,height:14 }}/> : null} Crear
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label" htmlFor="offset-gp">Punto de aforo <span className="req">*</span></label>
            <select id="offset-gp" className="form-select"
              value={createForm.gauge_point_id}
              onChange={(e) => setCreateForm((f) => ({ ...f, gauge_point_id: e.target.value }))}
            >
              <option value="">— Seleccionar —</option>
              {gaugePoints.map((gp) => <option key={gp.id} value={gp.id}>{gp.name}{gp.river ? ` · ${gp.river}` : ''}</option>)}
            </select>
            {createErrors.gauge_point_id && <span className="text-danger">{createErrors.gauge_point_id}</span>}
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="offset-dt">Tipo de Datum <span className="req">*</span></label>
            <select id="offset-dt" className="form-select"
              value={createForm.datum_type_id}
              onChange={(e) => setCreateForm((f) => ({ ...f, datum_type_id: e.target.value }))}
            >
              <option value="">— Seleccionar —</option>
              {datumTypes.map((dt) => <option key={dt.id} value={dt.id}>{dt.code} — {dt.name}</option>)}
            </select>
            {createErrors.datum_type_id && <span className="text-danger">{createErrors.datum_type_id}</span>}
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="offset-val">Corrección local → datum (m) <span className="req">*</span></label>
            <input id="offset-val" className="form-input mono" type="number" step="0.001"
              placeholder="Ej: 3.647"
              value={createForm.offset_local_to_datum}
              onChange={(e) => setCreateForm((f) => ({ ...f, offset_local_to_datum: e.target.value }))}
            />
            {createErrors.offset_local_to_datum && <span className="text-danger">{createErrors.offset_local_to_datum}</span>}
            <span className="form-hint">valor_datum = valor_local + corrección</span>

          </div>
        </Modal>
      )}

      {/* Modal editar */}
      {editing && (
        <Modal
          title={`Editar corrección — ${editing.gauge_point.name} / ${editing.datum_type.code}`}
          onClose={() => setEditing(null)}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setEditing(null)} disabled={updating}>Cancelar</button>
              <button className="btn btn-primary" onClick={handleUpdate} disabled={updating}>
                {updating ? <span className="spinner" style={{ width:14,height:14 }}/> : null} Guardar
              </button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label" htmlFor="edit-offset-val">Corrección local → datum (m)</label>
            <input id="edit-offset-val" className="form-input mono" type="number" step="0.001"
              value={updateForm.offset_local_to_datum}
              onChange={(e) => setUpdateForm({ offset_local_to_datum: e.target.value })}
            />
            {updateError && <span className="text-danger">{updateError}</span>}
            <span className="form-hint">valor_datum = valor_local + corrección</span>

          </div>
        </Modal>
      )}

      {deleting && (
        <ConfirmDialog
          title="Eliminar corrección"
          onConfirm={handleDelete}
          onCancel={() => setDeleting(null)}
          loading={deleteLoading}
        >
          ¿Eliminar la corrección de{' '}
          <span className="confirm-entity">{deleting.gauge_point.name}</span>{' '}
          hacia{' '}
          <span className="confirm-entity">{deleting.datum_type.code}</span>
          {' '}({deleting.offset_local_to_datum >= 0 ? '+' : ''}{deleting.offset_local_to_datum} m)?
        </ConfirmDialog>
      )}
    </>
  );
}

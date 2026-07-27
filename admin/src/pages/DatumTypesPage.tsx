import { useEffect, useState } from 'react';
import { Hash, Plus, Pencil, Trash2 } from 'lucide-react';
import { api } from '../services/adminApi';
import type { DatumType, DatumTypeCreate, DatumTypeUpdate } from '../services/adminApi';

import { Modal } from '../components/Modal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';

type FormData = { code: string; name: string; description: string };
const emptyForm = (): FormData => ({ code: '', name: '', description: '' });

export function DatumTypesPage() {
  const { show } = useToast();
  const [items, setItems] = useState<DatumType[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DatumType | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<DatumType | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<FormData>>({});

  const load = async () => {
    setLoading(true);
    try { setItems(await api.datumTypes.list()); }
    catch { show('Error al cargar ceros de referencia', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); setForm(emptyForm()); setErrors({}); setModalOpen(true); };
  const openEdit = (dt: DatumType) => {
    setEditing(dt);
    setForm({ code: dt.code, name: dt.name, description: dt.description ?? '' });
    setErrors({});
    setModalOpen(true);
  };

  const validate = (): boolean => {
    const e: Partial<FormData> = {};
    if (!editing && !form.code.trim()) e.code = 'El código es obligatorio';
    if (!form.name.trim()) e.name = 'El nombre es obligatorio';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      if (editing) {
        const body: DatumTypeUpdate = {
          name: form.name.trim() || undefined,
          description: form.description.trim() || undefined,
        };
        await api.datumTypes.update(editing.id, body);
        show('Tipo de datum actualizado');
      } else {
        const body: DatumTypeCreate = {
          code: form.code.trim().toUpperCase(),
          name: form.name.trim(),
          description: form.description.trim() || undefined,
        };
        await api.datumTypes.create(body);
        show('Tipo de datum creado');
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
      await api.datumTypes.delete(deleting.id);
      show('Tipo de datum eliminado');
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
          <h1 className="page-title">Ceros de Referencia</h1>
          <p className="page-subtitle">Tipos de datum disponibles en el sistema (ej: IGN, WHARTON).</p>
        </div>
        <button id="create-datum-type" className="btn btn-primary" onClick={openCreate}>
          <Plus size={15} /> Nuevo Datum
        </button>
      </div>

      <div className="page-body">
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Código</th>
                  <th>Nombre</th>
                  <th>Descripción</th>
                  <th style={{ textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr className="loading-row"><td colSpan={5}><div style={{ display:'flex',alignItems:'center',justifyContent:'center',gap:'0.5rem' }}><span className="spinner"/>Cargando…</div></td></tr>
                ) : items.length === 0 ? (
                  <tr><td colSpan={5}><div className="empty-state"><Hash size={28} className="empty-state__icon"/><div className="empty-state__title">Sin tipos de datum</div><div className="empty-state__desc">Creá el primero con el botón de arriba.</div></div></td></tr>
                ) : items.map((dt) => (
                  <tr key={dt.id}>
                    <td className="td-mono">#{dt.id}</td>
                    <td><span className="badge badge-code">{dt.code}</span></td>
                    <td className="td-primary">{dt.name}</td>
                    <td style={{ maxWidth: 280, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                      {dt.description ?? <span className="text-muted">—</span>}
                    </td>
                    <td>
                      <div className="td-actions">
                        <button id={`edit-dt-${dt.id}`} className="btn btn-ghost btn-sm" onClick={() => openEdit(dt)} title="Editar"><Pencil size={13}/></button>
                        <button id={`delete-dt-${dt.id}`} className="btn btn-ghost btn-sm" onClick={() => setDeleting(dt)} title="Eliminar" style={{ color:'var(--danger)' }}><Trash2 size={13}/></button>
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
          title={editing ? `Editar: ${editing.code}` : 'Nuevo Tipo de Datum'}
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
          {!editing && (
            <div className="form-group">
              <label className="form-label" htmlFor="dt-code">Código <span className="req">*</span></label>
              <input
                id="dt-code"
                className="form-input mono"
                placeholder="Ej: IGN"
                style={{ textTransform: 'uppercase' }}
                {...field('code')}
              />
              {errors.code && <span className="text-danger">{errors.code}</span>}
              <span className="form-hint">Se guardará en mayúsculas. No se puede modificar luego.</span>
            </div>
          )}
          <div className="form-group">
            <label className="form-label" htmlFor="dt-name">Nombre <span className="req">*</span></label>
            <input id="dt-name" className="form-input" placeholder="Ej: Instituto Geográfico Nacional" {...field('name')} />
            {errors.name && <span className="text-danger">{errors.name}</span>}
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="dt-desc">Descripción</label>
            <textarea id="dt-desc" className="form-textarea" placeholder="Descripción opcional…" {...field('description')} />
          </div>
        </Modal>
      )}

      {deleting && (
        <ConfirmDialog
          title="Eliminar Tipo de Datum"
          onConfirm={handleDelete}
          onCancel={() => setDeleting(null)}
          loading={deleteLoading}
        >
          ¿Eliminar el datum <span className="confirm-entity">"{deleting.code} — {deleting.name}"</span>?{' '}
          Se eliminarán también todos los offsets que lo referencien.
        </ConfirmDialog>
      )}
    </>
  );
}

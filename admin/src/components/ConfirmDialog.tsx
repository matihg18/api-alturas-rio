import type { ReactNode } from 'react';;
import { AlertTriangle } from 'lucide-react';
import { Modal } from './Modal';

interface Props {
  title: string;
  children: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
  danger?: boolean;
}

export function ConfirmDialog({ title, children, onConfirm, onCancel, loading, danger = true }: Props) {
  return (
    <Modal
      title={title}
      onClose={onCancel}
      size="sm"
      footer={
        <>
          <button className="btn btn-secondary" onClick={onCancel} disabled={loading}>Cancelar</button>
          <button
            className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : null}
            {danger ? 'Eliminar' : 'Confirmar'}
          </button>
        </>
      }
    >
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
        {danger && (
          <div style={{ color: 'var(--danger)', flexShrink: 0, marginTop: '0.1rem' }}>
            <AlertTriangle size={20} />
          </div>
        )}
        <div className="confirm-msg">{children}</div>
      </div>
    </Modal>
  );
}

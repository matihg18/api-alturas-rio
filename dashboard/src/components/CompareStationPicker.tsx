import React from 'react';
import { Station } from '../services/api';
import { Search, X } from 'lucide-react';

interface CompareStationPickerProps {
  /** Estación que ya está siendo visualizada (para excluirla de la lista) */
  currentStationId: number;
  allStations: Station[];
  onSelect: (station: Station) => void;
  onClose: () => void;
}

export const CompareStationPicker: React.FC<CompareStationPickerProps> = ({
  currentStationId,
  allStations,
  onSelect,
  onClose,
}) => {
  const [query, setQuery] = React.useState('');
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const filtered = React.useMemo(() => {
    const q = query.toLowerCase().trim();
    return allStations.filter(
      (s) =>
        s.id !== currentStationId &&
        (q === '' ||
          s.name.toLowerCase().includes(q) ||
          s.river.toLowerCase().includes(q)),
    );
  }, [allStations, currentStationId, query]);

  return (
    <div className="compare-picker" role="dialog" aria-label="Seleccionar estación para comparar">
      {/* Header */}
      <div className="compare-picker__header">
        <span className="compare-picker__title">Comparar con…</span>
        <button className="compare-picker__close" onClick={onClose} aria-label="Cerrar">
          <X size={14} />
        </button>
      </div>

      {/* Search */}
      <div className="compare-picker__search-wrap">
        <Search size={13} className="compare-picker__search-icon" />
        <input
          ref={inputRef}
          type="text"
          className="compare-picker__search"
          placeholder="Buscar por nombre o río…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {query && (
          <button className="compare-picker__search-clear" onClick={() => setQuery('')} aria-label="Limpiar búsqueda">
            <X size={11} />
          </button>
        )}
      </div>

      {/* List */}
      <div className="compare-picker__list">
        {filtered.length === 0 ? (
          <div className="compare-picker__empty">Sin resultados</div>
        ) : (
          filtered.map((s) => (
            <button
              key={s.id}
              className="compare-picker__item"
              onClick={() => onSelect(s)}
            >
              <span className="compare-picker__item-name">{s.name}</span>
              <span className="compare-picker__item-meta">
                Río {s.river} · {s.source}
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  );
};

import React from 'react';
import { Station, Measurement, LatestMeasurement, GaugePoint, apiClient } from '../services/api';
import { MapPin, Clock, Loader2, GitCompare, X as XIcon } from 'lucide-react';
import { CompareStationPicker } from './CompareStationPicker';

interface StationDetailProps {
  station: Station;
  /** Última medición en cero local (del polling de App.tsx) */
  latest: LatestMeasurement | null;
  /** Historial en cero local (del polling de App.tsx) */
  history: Measurement[];
  /** Lista global de estaciones para el picker de comparación */
  allStations: Station[];
}

// ── Tipos de comparación ──────────────────────────────────────────────────────
interface CompareEntry {
  station: Station;
  history: Measurement[];
  isLoading: boolean;
  /** Índice fijo en COMPARE_COLORS asignado al agregar. No cambia al eliminar otras. */
  colorIndex: number;
}

const MAX_COMPARE = 4; // máximo de estaciones adicionales (total = 5 con la principal)

// Paleta de colores para las series comparadas
const COMPARE_COLORS = ['#f97316', '#a855f7', '#22c55e', '#ec4899'];

// ─────────────────────────────────────────────────────────────────────────────

export const StationDetail: React.FC<StationDetailProps> = ({ station, latest, history, allStations }) => {
  const [gaugePoint, setGaugePoint] = React.useState<GaugePoint | null>(null);
  const [selectedDatum, setSelectedDatum] = React.useState<string | null>(null);
  const [isDatumLoading, setIsDatumLoading] = React.useState(false);
  const defaultDates = () => {
    const today = new Date();
    const monthAgo = new Date(today);
    monthAgo.setDate(today.getDate() - 30);
    return {
      from: monthAgo.toISOString().slice(0, 10),
      to: today.toISOString().slice(0, 10),
    };
  };

  const [fromDate, setFromDate] = React.useState(() => defaultDates().from);
  const [toDate, setToDate] = React.useState(() => defaultDates().to);
  const [isFiltered, setIsFiltered] = React.useState(false);
  const [isQueryLoading, setIsQueryLoading] = React.useState(false);
  const [displayLatest, setDisplayLatest] = React.useState<LatestMeasurement | null>(latest);
  const [displayHistory, setDisplayHistory] = React.useState<Measurement[]>(history);
  const [displayDatumUsed, setDisplayDatumUsed] = React.useState<string>('LOCAL');
  const [currentPage, setCurrentPage] = React.useState(1);
  const itemsPerPage = 20;

  // ── Comparación (múltiple) ────────────────────────────────────────────────
  const [showPicker, setShowPicker] = React.useState(false);
  const [compareEntries, setCompareEntries] = React.useState<CompareEntry[]>([]);

  const fetchCompareData = React.useCallback(async (
    stationId: number,
    from: string,
    to: string,
  ): Promise<Measurement[]> => {
    const chunkSize = 100;
    try {
      const first = await apiClient.getMeasurements(stationId, chunkSize, 0, undefined, from || undefined, to || undefined);
      const total = first.total_count;
      let allItems = [...first.items];

      if (total > chunkSize) {
        const pages = Math.ceil(total / chunkSize);
        const rest = await Promise.all(
          Array.from({ length: pages - 1 }, (_, i) =>
            apiClient.getMeasurements(stationId, chunkSize, (i + 1) * chunkSize, undefined, from || undefined, to || undefined)
          )
        );
        for (const page of rest) allItems = allItems.concat(page.items);
        allItems.sort((a, b) => new Date(a.date_time).getTime() - new Date(b.date_time).getTime());
      }

      return allItems;
    } catch (err) {
      console.error('Error al obtener mediciones de comparación:', err);
      return [];
    }
  }, []);

  // Agrega una nueva estación al array de comparación
  const handleSelectCompare = React.useCallback(async (s: Station) => {
    setShowPicker(false);

    // Elegir el primer índice de color que no esté en uso
    const usedIndices = new Set(compareEntries.map((e) => e.colorIndex));
    const colorIndex = COMPARE_COLORS.findIndex((_, i) => !usedIndices.has(i));

    // Marcar como cargando con el colorIndex ya asignado
    setCompareEntries((prev) => [...prev, { station: s, history: [], isLoading: true, colorIndex }]);

    const today = new Date();
    const monthAgo = new Date(today);
    monthAgo.setDate(today.getDate() - 30);
    const defaultFrom = monthAgo.toISOString().slice(0, 10);

    const items = await fetchCompareData(s.id, fromDate || defaultFrom, toDate);

    setCompareEntries((prev) =>
      prev.map((entry) =>
        entry.station.id === s.id ? { ...entry, history: items, isLoading: false } : entry
      )
    );
  }, [fromDate, toDate, fetchCompareData, compareEntries]);

  // Quita una estación comparada por su ID
  const handleRemoveCompare = React.useCallback((stationId: number) => {
    setCompareEntries((prev) => prev.filter((e) => e.station.id !== stationId));
  }, []);
  // ─────────────────────────────────────────────────────────────────────────────

  const fetchRecent = React.useCallback(async (datumCode: string | null) => {
    const today = new Date();
    const monthAgo = new Date(today);
    monthAgo.setDate(today.getDate() - 30);
    const fromIso = monthAgo.toISOString().slice(0, 10);

    setIsQueryLoading(true);
    try {
      const result = await apiClient.getMeasurements(
        station.id,
        100,
        0,
        datumCode || undefined,
        fromIso,
        undefined,
      );
      if (datumCode) setDisplayDatumUsed(result.datum_used);
      setDisplayHistory(result.items);
    } catch (err) {
      console.error('Error al obtener mediciones recientes:', err);
    } finally {
      setIsQueryLoading(false);
    }
  }, [station.id]);

  const fetchAll = React.useCallback(async (
    datumCode: string | null,
    from: string,
    to: string,
  ) => {
    const chunkSize = 100;
    setIsQueryLoading(true);
    try {
      const first = await apiClient.getMeasurements(
        station.id,
        chunkSize,
        0,
        datumCode || undefined,
        from || undefined,
        to || undefined,
      );
      if (datumCode) setDisplayDatumUsed(first.datum_used);

      const total = first.total_count;
      let allItems = [...first.items];

      if (total > chunkSize) {
        const pages = Math.ceil(total / chunkSize);
        const rest = await Promise.all(
          Array.from({ length: pages - 1 }, (_, i) =>
            apiClient.getMeasurements(
              station.id,
              chunkSize,
              (i + 1) * chunkSize,
              datumCode || undefined,
              from || undefined,
              to || undefined,
            )
          )
        );
        for (const page of rest) allItems = allItems.concat(page.items);
        allItems.sort((a, b) => new Date(a.date_time).getTime() - new Date(b.date_time).getTime());
      }

      setDisplayHistory(allItems);
    } catch (err) {
      console.error('Error al obtener mediciones:', err);
    } finally {
      setIsQueryLoading(false);
    }
  }, [station.id]);

  React.useEffect(() => {
    setSelectedDatum(null);
    setGaugePoint(null);
    setCurrentPage(1);
    const dates = defaultDates();
    setFromDate(dates.from);
    setToDate(dates.to);
    setIsFiltered(false);
    setDisplayLatest(latest);
    setDisplayDatumUsed('LOCAL');
    // Limpiar comparaciones al cambiar de estación
    setCompareEntries([]);
    setShowPicker(false);

    if (station.gauge_point_id !== null) {
      apiClient.getGaugePoint(station.id)
        .then(setGaugePoint)
        .catch(() => setGaugePoint(null));
    }
  }, [station.id]);

  React.useEffect(() => {
    fetchRecent(null);
  }, [station.id]);

  React.useEffect(() => {
    if (selectedDatum === null && !isFiltered) {
      setDisplayLatest(latest);
      setDisplayDatumUsed('LOCAL');
    }
  }, [latest, selectedDatum, isFiltered]);

  const handleDatumChange = async (datumCode: string | null) => {
    if (datumCode === selectedDatum) return;
    setSelectedDatum(datumCode);
    setCurrentPage(1);

    if (datumCode === null) {
      setDisplayLatest(latest);
      setDisplayDatumUsed('LOCAL');
      if (isFiltered) {
        await fetchAll(null, fromDate, toDate);
      } else {
        await fetchRecent(null);
      }
      return;
    }

    setIsDatumLoading(true);
    try {
      const latestResult = await apiClient.getLatestMeasurement(station.id, datumCode);
      setDisplayLatest(latestResult);
      setDisplayDatumUsed(latestResult.datum_used);
    } catch (err) {
      console.error('Error al obtener última medición con datum:', err);
      setSelectedDatum(null);
      setDisplayLatest(latest);
      setDisplayDatumUsed('LOCAL');
    } finally {
      setIsDatumLoading(false);
    }
    if (isFiltered) {
      await fetchAll(datumCode, fromDate, toDate);
    } else {
      await fetchRecent(datumCode);
    }
  };

  const handleQuery = async () => {
    if (!fromDate && !toDate) return;
    setIsFiltered(true);
    setCurrentPage(1);
    await fetchAll(selectedDatum, fromDate, toDate);

    // Actualizar todas las comparaciones con el mismo rango
    if (compareEntries.length > 0) {
      setCompareEntries((prev) => prev.map((e) => ({ ...e, isLoading: true })));
      const updated = await Promise.all(
        compareEntries.map(async (entry) => {
          const items = await fetchCompareData(entry.station.id, fromDate, toDate);
          return { ...entry, history: items, isLoading: false };
        })
      );
      setCompareEntries(updated);
    }
  };

  const handleClear = async () => {
    const dates = defaultDates();
    setFromDate(dates.from);
    setToDate(dates.to);
    setIsFiltered(false);
    setCurrentPage(1);
    await fetchRecent(selectedDatum);

    // Volver a los últimos 30 días para todas las comparaciones
    if (compareEntries.length > 0) {
      setCompareEntries((prev) => prev.map((e) => ({ ...e, isLoading: true })));
      const updated = await Promise.all(
        compareEntries.map(async (entry) => {
          const items = await fetchCompareData(entry.station.id, dates.from, '');
          return { ...entry, history: items, isLoading: false };
        })
      );
      setCompareEntries(updated);
    }
  };

  const formatDate = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleString('es-AR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const formatXLabel = (isoString: string): string => {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: '2-digit' });
  };

  // ── Chart geometry ────────────────────────────────────────────────────────────
  const chartWidth = 1000;
  const chartHeight = 280;
  const chartPadding = { top: 20, right: 20, bottom: 35, left: 40 };

  const hasChart = displayHistory.length > 0;

  // Calcular rango de tiempo global (todas las series)
  const allTimestamps = [
    ...displayHistory.map((m) => new Date(m.date_time).getTime()),
    ...compareEntries.flatMap((e) => e.history.map((m) => new Date(m.date_time).getTime())),
  ];
  const tMin = allTimestamps.length > 0 ? Math.min(...allTimestamps) : 0;
  const tMax = allTimestamps.length > 0 ? Math.max(...allTimestamps) : 1;
  const tRange = tMax - tMin || 1;

  // Rango Y unificado entre todas las series
  const primaryValues = displayHistory.map((m) => m.value);
  const compareValues = compareEntries.flatMap((e) => e.history.map((m) => m.value));

  const allValues = compareEntries.length > 0 ? [...primaryValues, ...compareValues] : primaryValues;
  const minVal = allValues.length > 0 ? Math.min(...allValues) : 0;
  const maxVal = allValues.length > 0 ? Math.max(...allValues) : 12;
  const yRange = maxVal - minVal || 1;

  const getChartX = (ts: number): number => {
    if (tRange === 0) return chartPadding.left;
    return chartPadding.left + ((ts - tMin) / tRange) * (chartWidth - chartPadding.left - chartPadding.right);
  };

  const getChartY = (val: number): number => {
    const h = chartHeight - chartPadding.top - chartPadding.bottom;
    return chartHeight - chartPadding.bottom - ((val - minVal) / yRange) * h;
  };

  // Primary series points (time-based X)
  const primaryPoints = displayHistory.map((m) => ({
    x: getChartX(new Date(m.date_time).getTime()),
    y: getChartY(m.value),
    value: m.value,
    ts: m.date_time,
  }));

  // Compare series points — un array de puntos por cada entrada
  const comparePointsArr = compareEntries.map((entry) =>
    entry.history.map((m) => ({
      x: getChartX(new Date(m.date_time).getTime()),
      y: getChartY(m.value),
      value: m.value,
      ts: m.date_time,
    }))
  );

  const makePath = (pts: { x: number; y: number }[]) =>
    pts.length > 0 ? `M ${pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ')}` : '';

  const makeArea = (pts: { x: number; y: number }[], linePath: string) => {
    if (pts.length === 0) return '';
    const bottom = getChartY(minVal);
    return `${linePath} L ${pts[pts.length - 1].x.toFixed(1)},${bottom.toFixed(1)} L ${pts[0].x.toFixed(1)},${bottom.toFixed(1)} Z`;
  };

  const primaryLinePath = makePath(primaryPoints);
  const primaryAreaPath = makeArea(primaryPoints, primaryLinePath);

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => parseFloat((minVal + f * yRange).toFixed(1)));

  // X-axis ticks derived from unified time range
  const xTickCount = 7;
  const xTickTimes = Array.from({ length: xTickCount }, (_, i) =>
    tMin + (i / (xTickCount - 1)) * tRange
  );

  // Hover
  const svgRef = React.useRef<SVGSVGElement>(null);
  const [hoverX, setHoverX] = React.useState<number | null>(null);

  const handleSvgMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const rawX = ((e.clientX - rect.left) / rect.width) * chartWidth;
    setHoverX(rawX);
  };

  // Cursor X → timestamp real
  const hoverTimestamp = React.useMemo(() => {
    if (hoverX === null) return null;
    const drawWidth = chartWidth - chartPadding.left - chartPadding.right;
    return tMin + ((hoverX - chartPadding.left) / drawWidth) * tRange;
  }, [hoverX, tMin, tRange]);

  // Punto más cercano de la serie principal
  const closestPrimary = React.useMemo(() => {
    if (hoverTimestamp === null || primaryPoints.length === 0) return null;
    return primaryPoints.reduce((best, p) =>
      Math.abs(new Date(p.ts).getTime() - hoverTimestamp) <
      Math.abs(new Date(best.ts).getTime() - hoverTimestamp)
        ? p
        : best
    );
  }, [hoverTimestamp, primaryPoints]);

  // Punto más cercano de cada serie comparada
  const closestCompareArr = React.useMemo(() => {
    if (hoverTimestamp === null) return [];
    return comparePointsArr.map((pts) => {
      if (pts.length === 0) return null;
      return pts.reduce((best, p) =>
        Math.abs(new Date(p.ts).getTime() - hoverTimestamp) <
        Math.abs(new Date(best.ts).getTime() - hoverTimestamp)
          ? p
          : best
      );
    });
  }, [hoverTimestamp, comparePointsArr]);

  const isHoverActive = hoverX !== null &&
    hoverX >= chartPadding.left &&
    hoverX <= chartWidth - chartPadding.right;

  // ── Tabla ─────────────────────────────────────────────────────────────────────
  const sortedHistory = React.useMemo(
    () => [...displayHistory].sort((a, b) => new Date(b.date_time).getTime() - new Date(a.date_time).getTime()),
    [displayHistory]
  );
  const totalPages = Math.ceil(sortedHistory.length / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedHistory = sortedHistory.slice(startIndex, startIndex + itemsPerPage);

  const datumLabel = selectedDatum === null
    ? 'Cero Local'
    : (gaugePoint?.datums.find(d => d.datum_type.code === selectedDatum)?.datum_type.name ?? selectedDatum);

  // Colores
  const COLOR_PRIMARY = 'var(--accent-blue)';

  // IDs a excluir del picker: estación principal + todas las ya comparadas
  const excludedIds = [station.id, ...compareEntries.map((e) => e.station.id)];

  // Hay alguna comparación cargando
  const isAnyCompareLoading = compareEntries.some((e) => e.isLoading);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>

      <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
            <MapPin size={13} />
            <span>Río {station.river}</span>
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: '500', color: 'var(--text-primary)', marginTop: '0.2rem' }}>
            {station.name}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
            <Clock size={12} />
            <span>Última lectura: {displayLatest ? formatDate(displayLatest.date_time) : '—'}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>

        <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: '250px', padding: '2rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Nivel de Agua Observado
          </span>

          <div style={{ margin: '0.8rem 0', display: 'flex', alignItems: 'flex-end', gap: '6px' }}>
            {displayLatest !== null ? (
              <>
                <span className="mono" style={{ fontSize: '3rem', fontWeight: '700', color: 'var(--text-primary)', lineHeight: '1' }}>
                  {displayLatest.value.toFixed(2)}
                </span>
                <span style={{ fontSize: '1.2rem', color: 'var(--accent-blue)', fontWeight: '600', marginBottom: '4px' }}>m</span>
              </>
            ) : (
              <span style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>Sin datos</span>
            )}
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.2rem', marginTop: '0.5rem' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.6rem' }}>
              <span>Cero de Referencia</span>
              {isDatumLoading && <Loader2 size={12} className="spin" style={{ color: 'var(--accent-blue)' }} />}
            </span>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', background: '#090D16', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '2px', width: 'fit-content' }}>
              {renderDatumButton(
                'LOCAL',
                'Cero Local',
                selectedDatum === null,
                false,
                () => handleDatumChange(null),
              )}

              {gaugePoint !== null
                ? gaugePoint.datums.map((gd) =>
                  renderDatumButton(
                    gd.datum_type.code,
                    gd.datum_type.name,
                    selectedDatum === gd.datum_type.code,
                    false,
                    () => handleDatumChange(gd.datum_type.code),
                  )
                )
                : station.gauge_point_id === null
                  ? null
                  : (
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', padding: '0.45rem 0.6rem' }}>
                      Cargando datums…
                    </span>
                  )
              }
            </div>

            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.5rem' }}>
              {selectedDatum === null
                ? 'Referencia al cero local de la escala física de la estación.'
                : `Mostrando valores referenciados al datum: ${displayDatumUsed}.`}
              {station.gauge_point_id === null && (
                <> Esta estación no tiene datos de conversión altimétrica.</>
              )}
            </span>
          </div>
        </div>

        <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', minHeight: '250px' }}>
          <h3 style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.02em', marginBottom: '1.2rem' }}>
            Parámetros de Referencia
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <Row label="Río" value={`Río ${station.river}`} />
            <Row label="Fuente" value={station.source} />
            <Row label="Latitud" value={station.latitud != null ? `${Math.abs(station.latitud).toFixed(4)}° S` : '—'} mono />
            <Row label="Longitud" value={station.longitud != null ? `${Math.abs(station.longitud).toFixed(4)}° O` : '—'} mono />
            {station.alert_value != null && (
              <Row label="Nivel de alerta" value={`${station.alert_value.toFixed(2)} m`} mono color="#f59e0b" />
            )}
            {station.evacuation_value != null && (
              <Row label="Nivel de evacuación" value={`${station.evacuation_value.toFixed(2)} m`} mono color="#ef4444" last />
            )}
          </div>
        </div>
      </div>

      <div className="card-panel">
        {/* Header de la sección con botón de comparación */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.2rem', flexWrap: 'wrap', gap: '0.8rem' }}>
          <h3 style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.02em', marginTop: '0.1rem' }}>
            Evolución del Nivel
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', position: 'relative' }}>
            {/* Badges de estaciones comparadas */}
            {compareEntries.map((entry) => (
              <div className="compare-badge" key={entry.station.id}>
                <span
                  className="compare-badge__dot"
                  style={{ background: COMPARE_COLORS[entry.colorIndex] }}
                />
                <span className="compare-badge__name">{entry.station.name}</span>
                {entry.isLoading && <Loader2 size={11} className="spin" style={{ color: COMPARE_COLORS[entry.colorIndex] }} />}
                <button
                  className="compare-badge__remove"
                  onClick={() => handleRemoveCompare(entry.station.id)}
                  aria-label={`Quitar ${entry.station.name}`}
                >
                  <XIcon size={11} />
                </button>
              </div>
            ))}

            {/* Botón comparar — visible mientras no se alcance el límite */}
            {compareEntries.length < MAX_COMPARE && (
              <div style={{ position: 'relative' }}>
                <button
                  className={`btn btn-compare${showPicker ? ' btn-compare--active' : ''}`}
                  onClick={() => setShowPicker((v) => !v)}
                  title="Agregar estación para comparar"
                >
                  <GitCompare size={13} />
                  <span>Comparar</span>
                </button>

                {showPicker && (
                  <CompareStationPicker
                    excludedIds={excludedIds}
                    allStations={allStations}
                    onSelect={handleSelectCompare}
                    onClose={() => setShowPicker(false)}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Leyenda de series (visible cuando hay al menos una comparación) */}
        {compareEntries.length > 0 && (
          <div className="compare-legend">
            <div className="compare-legend__item">
              <span className="compare-legend__dot" style={{ background: COLOR_PRIMARY }} />
              <span className="compare-legend__label">{station.name}</span>
              <span className="compare-legend__sub">cero local</span>
            </div>
            {compareEntries.map((entry) => (
              <div className="compare-legend__item" key={entry.station.id}>
                <span className="compare-legend__dot" style={{ background: COMPARE_COLORS[entry.colorIndex] }} />
                <span className="compare-legend__label">{entry.station.name}</span>
                <span className="compare-legend__sub">cero local</span>
              </div>
            ))}
          </div>
        )}

        {/* Filtro de fechas */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1rem',
          alignItems: 'flex-end',
          marginBottom: '1.5rem',
          background: 'rgba(255, 255, 255, 0.01)',
          border: '1px solid var(--border-color)',
          borderRadius: '4px',
          padding: '1rem',
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', flex: '1 1 180px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: '500' }}>Fecha Desde</span>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '3px',
                padding: '0.4rem 0.6rem',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
                outline: 'none',
                width: '100%',
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', flex: '1 1 180px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: '500' }}>Fecha Hasta</span>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '3px',
                padding: '0.4rem 0.6rem',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
                outline: 'none',
                width: '100%',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              onClick={handleQuery}
              disabled={isQueryLoading || isDatumLoading || (!fromDate && !toDate)}
              className="btn"
              style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', height: '34px' }}
            >
              {isQueryLoading ? 'Consultando...' : 'Consultar'}
            </button>

            {isFiltered && (
              <button
                onClick={handleClear}
                disabled={isQueryLoading || isDatumLoading}
                className="btn btn-secondary"
                style={{ padding: '0.4rem 1rem', fontSize: '0.8rem', height: '34px' }}
              >
                Limpiar
              </button>
            )}
          </div>
        </div>

        {!hasChart ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            Sin registros históricos disponibles para este período.
          </div>
        ) : (
          <div style={{
            position: 'relative',
            width: '100%',
            overflowX: 'auto',
            background: '#090D16',
            border: '1px solid var(--border-color)',
            borderRadius: '2px',
            padding: '10px'
          }}>
            {(isDatumLoading || isAnyCompareLoading) && (
              <div style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.3rem 0.6rem',
                background: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid var(--border-color)',
                borderRadius: '4px',
                fontSize: '0.65rem',
                color: 'var(--text-secondary)',
                zIndex: 10
              }}>
                <Loader2 size={12} className="spin" style={{ color: 'var(--accent-blue)' }} />
                <span>{isDatumLoading ? 'Convirtiendo datum...' : 'Cargando comparación...'}</span>
              </div>
            )}
            <svg
              ref={svgRef}
              key={station.id}
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              style={{ width: '100%', height: 'auto', aspectRatio: `${chartWidth} / ${chartHeight}`, overflow: 'visible', minWidth: '450px', cursor: 'crosshair' }}
              onMouseMove={handleSvgMouseMove}
              onMouseLeave={() => setHoverX(null)}
            >
              <defs>
                <linearGradient id="area-grad-primary" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor={COLOR_PRIMARY} stopOpacity="0.12" />
                  <stop offset="100%" stopColor={COLOR_PRIMARY} stopOpacity="0.0" />
                </linearGradient>
                {compareEntries.map((entry) => {
                  const color = COMPARE_COLORS[entry.colorIndex];
                  return (
                    <linearGradient key={entry.colorIndex} id={`area-grad-compare-${entry.colorIndex}`} x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor={color} stopOpacity="0.10" />
                      <stop offset="100%" stopColor={color} stopOpacity="0.0" />
                    </linearGradient>
                  );
                })}
              </defs>

              {/* Grid Y */}
              {yTicks.map((tickVal, tickIdx) => {
                const y = getChartY(tickVal);
                return (
                  <g key={`grid-${tickIdx}`}>
                    <line x1={chartPadding.left} y1={y} x2={chartWidth - chartPadding.right} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
                    <text x={chartPadding.left - 6} y={y + 3} textAnchor="end" fill="var(--text-muted)" className="mono" style={{ fontSize: '0.6rem' }}>
                      {tickVal.toFixed(1)}m
                    </text>
                  </g>
                );
              })}

              {/* Grid X ticks (tiempo real) */}
              {xTickTimes.map((t, i) => {
                const x = getChartX(t);
                const anchor = i === 0 ? 'start' : i === xTickCount - 1 ? 'end' : 'middle';
                return (
                  <g key={`x-lbl-${i}`}>
                    <line x1={x} y1={chartHeight - chartPadding.bottom} x2={x} y2={chartHeight - chartPadding.bottom + 4} stroke="rgba(255,255,255,0.1)" strokeWidth="0.8" />
                    <text x={x} y={chartHeight - chartPadding.bottom + 15} textAnchor={anchor} fill="var(--text-muted)" className="mono" style={{ fontSize: '0.6rem' }}>
                      {formatXLabel(new Date(t).toISOString())}
                    </text>
                  </g>
                );
              })}

              {/* Áreas y líneas — series comparadas (debajo de la principal) */}
              {compareEntries.map((entry, idx) => {
                const pts = comparePointsArr[idx];
                if (pts.length === 0) return null;
                const color = COMPARE_COLORS[entry.colorIndex];
                const linePath = makePath(pts);
                const areaPath = makeArea(pts, linePath);
                return (
                  <g key={entry.station.id}>
                    {areaPath && <path d={areaPath} fill={`url(#area-grad-compare-${entry.colorIndex})`} />}
                    {linePath && (
                      <path d={linePath} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.85" />
                    )}
                  </g>
                );
              })}

              {/* Área y línea — serie principal */}
              {primaryAreaPath && <path d={primaryAreaPath} fill="url(#area-grad-primary)" />}
              {primaryLinePath && (
                <path d={primaryLinePath} fill="none" stroke={COLOR_PRIMARY} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              )}

              {/* Puntos fijos al final de cada serie (solo cuando NO hay hover) */}
              {!isHoverActive && primaryPoints.length > 0 && (
                <circle
                  cx={primaryPoints[primaryPoints.length - 1].x}
                  cy={primaryPoints[primaryPoints.length - 1].y}
                  r="3" fill="var(--text-primary)" stroke={COLOR_PRIMARY} strokeWidth="1"
                />
              )}
              {!isHoverActive && compareEntries.map((entry, idx) => {
                const pts = comparePointsArr[idx];
                if (pts.length === 0) return null;
                const color = COMPARE_COLORS[entry.colorIndex];
                return (
                  <circle
                    key={entry.station.id}
                    cx={pts[pts.length - 1].x}
                    cy={pts[pts.length - 1].y}
                    r="3" fill="var(--text-primary)" stroke={color} strokeWidth="1"
                  />
                );
              })}

              {/* Línea de cursor vertical + etiqueta de tiempo + círculos de hover */}
              {isHoverActive && hoverX !== null && (
                <g>
                  {/* Línea vertical en el X del cursor */}
                  <line
                    x1={hoverX}
                    y1={chartPadding.top}
                    x2={hoverX}
                    y2={chartHeight - chartPadding.bottom}
                    stroke="rgba(255,255,255,0.18)"
                    strokeWidth="1"
                    strokeDasharray="3 3"
                  />
                  {/* Etiqueta de fecha en el cursor (en el eje X) */}
                  {hoverTimestamp !== null && (() => {
                    const label = formatXLabel(new Date(hoverTimestamp).toISOString());
                    const lx = Math.min(
                      Math.max(hoverX, chartPadding.left + 20),
                      chartWidth - chartPadding.right - 20,
                    );
                    return (
                      <>
                        <rect
                          x={lx - 18} y={chartHeight - chartPadding.bottom + 4}
                          width={36} height={11}
                          fill="rgba(14,20,35,0.9)" rx="2"
                        />
                        <text
                          x={lx} y={chartHeight - chartPadding.bottom + 13}
                          textAnchor="middle"
                          fill="rgba(255,255,255,0.55)"
                          className="mono"
                          style={{ fontSize: '0.5rem' }}
                        >
                          {label}
                        </text>
                      </>
                    );
                  })()}
                  {/* Círculo de hover — serie principal */}
                  {closestPrimary && (
                    <circle cx={closestPrimary.x} cy={closestPrimary.y} r="5" fill="var(--text-primary)" stroke={COLOR_PRIMARY} strokeWidth="1.5" />
                  )}
                  {/* Círculos de hover — series comparadas */}
                  {closestCompareArr.map((pt, idx) => {
                    if (!pt) return null;
                    const color = COMPARE_COLORS[compareEntries[idx]?.colorIndex ?? idx];
                    return (
                      <circle key={idx} cx={pt.x} cy={pt.y} r="5" fill="var(--text-primary)" stroke={color} strokeWidth="1.5" />
                    );
                  })}
                </g>
              )}

              {/* Tooltip */}
              {isHoverActive && hoverX !== null && (() => {
                const activeSeries: Array<{ value: number; ts: string; color: string; name: string }> = [];
                if (closestPrimary) activeSeries.push({ value: closestPrimary.value, ts: closestPrimary.ts, color: COLOR_PRIMARY, name: station.name });
                closestCompareArr.forEach((pt, idx) => {
                  if (pt) activeSeries.push({
                    value: pt.value,
                    ts: pt.ts,
                    color: COMPARE_COLORS[compareEntries[idx]?.colorIndex ?? idx],
                    name: compareEntries[idx]?.station.name ?? '',
                  });
                });
                if (activeSeries.length === 0) return null;

                const rowH = 30;
                const tw = 175;
                const th = activeSeries.length * rowH + 6;
                const tx = hoverX > chartWidth - tw - 14 ? hoverX - tw - 8 : hoverX + 8;
                const midY = activeSeries.reduce((sum, _, i) => {
                  const pt = i === 0 ? closestPrimary : closestCompareArr[i - 1];
                  return sum + (pt?.y ?? 0);
                }, 0) / activeSeries.length;
                const ty = midY < th + 10 ? midY + 15 : midY - th - 10;

                return (
                  <g style={{ pointerEvents: 'none' }}>
                    <rect x={tx} y={ty} width={tw} height={th} fill="#0F172A" stroke="var(--border-color)" strokeWidth="1" rx="4" />
                    {activeSeries.map((s, i) => {
                      const rowY = ty + 6 + i * rowH;
                      return (
                        <g key={i}>
                          <circle cx={tx + 10} cy={rowY + 8} r="3" fill={s.color} />
                          <text x={tx + 19} y={rowY + 12} fill="var(--text-primary)" className="mono" style={{ fontSize: '0.65rem', fontWeight: 'bold' }}>
                            {s.value.toFixed(2)}m
                          </text>
                          <text x={tx + 19} y={rowY + 24} fill="var(--text-secondary)" style={{ fontSize: '0.52rem' }}>
                            {formatDate(s.ts)}
                          </text>
                        </g>
                      );
                    })}
                  </g>
                );
              })()}
            </svg>
          </div>
        )}
      </div>

      <div className="card-panel">
        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
            Historial de Mediciones — {datumLabel}
          </span>
          <span className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
            Pág. {currentPage} de {totalPages}
          </span>
        </div>

        {sortedHistory.length === 0 ? (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', padding: '1rem 0' }}>
            Sin registros para mostrar.
          </p>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                    <th style={{ textAlign: 'left', padding: '0.6rem 0.4rem', fontWeight: '600' }}>Fecha y Hora</th>
                    <th style={{ textAlign: 'right', padding: '0.6rem 0.4rem', fontWeight: '600' }}>
                      Altura (m)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {isQueryLoading ? (
                    <tr>
                      <td colSpan={2} style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        Cargando…
                      </td>
                    </tr>
                  ) : paginatedHistory.map((m) => (
                    <tr key={m.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <td style={{ padding: '0.6rem 0.4rem', color: 'var(--text-secondary)' }}>{formatDate(m.date_time)}</td>
                      <td className="mono" style={{ textAlign: 'right', padding: '0.6rem 0.4rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {m.value.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.2rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Mostrando {sortedHistory.length === 0 ? 0 : startIndex + 1}–{Math.min(startIndex + itemsPerPage, sortedHistory.length)} de {sortedHistory.length} registros
              </span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1 || isQueryLoading} className="btn btn-secondary" style={{ padding: '0.35rem 0.7rem', fontSize: '0.75rem' }}>
                  Anterior
                </button>
                <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages || isQueryLoading} className="btn btn-secondary" style={{ padding: '0.35rem 0.7rem', fontSize: '0.75rem' }}>
                  Siguiente
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderDatumButton(
  code: string,
  label: string,
  active: boolean,
  disabled: boolean,
  onClick: () => void,
) {
  return (
    <button
      key={code}
      onClick={onClick}
      disabled={disabled}
      title={disabled ? 'Sin datos de conversión para esta estación' : undefined}
      style={{
        background: active ? 'var(--accent-blue)' : 'transparent',
        color: active ? '#ffffff' : disabled ? 'var(--text-muted)' : 'var(--text-secondary)',
        border: 'none',
        borderRadius: '3px',
        padding: '0.45rem 0.9rem',
        fontSize: '0.75rem',
        fontWeight: active ? '600' : '500',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        transition: 'all 0.15s ease',
        whiteSpace: 'nowrap',
      }}
    >
      {label}
    </button>
  );
}

interface RowProps {
  label: string;
  value: string;
  mono?: boolean;
  color?: string;
  last?: boolean;
}

function Row({ label, value, mono, color, last }: RowProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: last ? 'none' : '1px solid var(--border-color)', paddingBottom: '0.4rem' }}>
      <span>{label}:</span>
      <span className={mono ? 'mono' : undefined} style={{ color: color ?? 'var(--text-primary)', fontWeight: '500' }}>
        {value}
      </span>
    </div>
  );
}

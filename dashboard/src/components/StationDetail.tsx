import React from 'react';
import { Station, Measurement, LatestMeasurement, GaugePoint, apiClient } from '../services/api';
import { MapPin, Clock, Loader2 } from 'lucide-react';

interface StationDetailProps {
  station: Station;
  /** Última medición en cero local (del polling de App.tsx) */
  latest: LatestMeasurement | null;
  /** Historial en cero local (del polling de App.tsx) */
  history: Measurement[];
}

export const StationDetail: React.FC<StationDetailProps> = ({ station, latest, history }) => {
  const [gaugePoint, setGaugePoint] = React.useState<GaugePoint | null>(null);
  const [selectedDatum, setSelectedDatum] = React.useState<string | null>(null);
  const [isDatumLoading, setIsDatumLoading] = React.useState(false);
  const [fromDate, setFromDate] = React.useState('');
  const [toDate, setToDate] = React.useState('');
  const [isFiltered, setIsFiltered] = React.useState(false);
  const [isQueryLoading, setIsQueryLoading] = React.useState(false);
  const [displayLatest, setDisplayLatest] = React.useState<LatestMeasurement | null>(latest);
  const [displayHistory, setDisplayHistory] = React.useState<Measurement[]>(history);
  const [displayDatumUsed, setDisplayDatumUsed] = React.useState<string>('LOCAL');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [hoveredPoint, setHoveredPoint] = React.useState<null | {
    x: number; y: number; height: number; timestamp: string;
  }>(null);
  const itemsPerPage = 20;

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
    setFromDate('');
    setToDate('');
    setIsFiltered(false);
    setDisplayLatest(latest);
    setDisplayDatumUsed('LOCAL');

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
  };

  const handleClear = async () => {
    setFromDate('');
    setToDate('');
    setIsFiltered(false);
    setCurrentPage(1);
    await fetchRecent(selectedDatum);
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

  const chartWidth = 1000;
  const chartHeight = 280;
  const chartPadding = { top: 20, right: 20, bottom: 35, left: 40 };

  const hasChart = displayHistory.length > 0;
  const values = displayHistory.map((m) => m.value);
  const minVal = hasChart ? Math.min(...values) : 0;
  const maxVal = hasChart ? Math.max(...values) : 12;
  const yRange = maxVal - minVal || 1;

  const getChartX = (index: number, total: number) => {
    if (total <= 1) return chartPadding.left;
    return chartPadding.left + (index / (total - 1)) * (chartWidth - chartPadding.left - chartPadding.right);
  };
  const getChartY = (val: number) => {
    const h = chartHeight - chartPadding.top - chartPadding.bottom;
    return chartHeight - chartPadding.bottom - ((val - minVal) / yRange) * h;
  };

  const chartPoints = displayHistory.map((m, i) => ({
    x: getChartX(i, displayHistory.length),
    y: getChartY(m.value),
  }));

  const sliceWidth = chartPoints.length > 1
    ? (chartWidth - chartPadding.left - chartPadding.right) / (chartPoints.length - 1)
    : chartWidth;

  const linePath = chartPoints.length > 0
    ? `M ${chartPoints.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ')}`
    : '';
  const areaPath = chartPoints.length > 0
    ? `${linePath} L ${chartPoints[chartPoints.length - 1].x.toFixed(1)},${getChartY(minVal).toFixed(1)} L ${chartPoints[0].x.toFixed(1)},${getChartY(minVal).toFixed(1)} Z`
    : '';

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => parseFloat((minVal + f * yRange).toFixed(1)));

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
        <h3 style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.02em', marginBottom: '1.2rem' }}>
          Evolución del Nivel
        </h3>
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

            {(isFiltered || fromDate || toDate) && (
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
            {isDatumLoading && (
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
                <span>Convirtiendo datum...</span>
              </div>
            )}
            <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: '100%', height: 'auto', aspectRatio: `${chartWidth} / ${chartHeight}`, overflow: 'visible', minWidth: '450px' }}>
              <defs>
                <linearGradient id="area-grad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="var(--accent-blue)" stopOpacity="0.08" />
                  <stop offset="100%" stopColor="var(--accent-blue)" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {yTicks.map((tickVal) => {
                const y = getChartY(tickVal);
                return (
                  <g key={`grid-${tickVal}`}>
                    <line x1={chartPadding.left} y1={y} x2={chartWidth - chartPadding.right} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
                    <text x={chartPadding.left - 6} y={y + 3} textAnchor="end" fill="var(--text-muted)" className="mono" style={{ fontSize: '0.6rem' }}>
                      {tickVal.toFixed(1)}m
                    </text>
                  </g>
                );
              })}

              {areaPath && <path d={areaPath} fill="url(#area-grad)" />}
              {linePath && <path d={linePath} fill="none" stroke="var(--accent-blue)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />}

              {chartPoints.length > 0 && (
                <circle cx={chartPoints[chartPoints.length - 1].x} cy={chartPoints[chartPoints.length - 1].y} r="3" fill="var(--text-primary)" stroke="var(--accent-blue)" strokeWidth="1" />
              )}

              {hoveredPoint && (
                <g>
                  <line x1={hoveredPoint.x} y1={chartPadding.top} x2={hoveredPoint.x} y2={chartHeight - chartPadding.bottom} stroke="var(--accent-blue)" strokeWidth="0.8" strokeDasharray="2 3" />
                  <circle cx={hoveredPoint.x} cy={hoveredPoint.y} r="5" fill="var(--text-primary)" stroke="var(--accent-blue)" strokeWidth="1.5" />
                </g>
              )}

              {displayHistory.length > 1 && (() => {
                const n = Math.min(8, displayHistory.length);
                const tickIndices = Array.from({ length: n }, (_, i) =>
                  i === 0 ? 0
                    : i === n - 1 ? displayHistory.length - 1
                      : Math.round((i / (n - 1)) * (displayHistory.length - 1))
                );
                return tickIndices.map((idx, tickPos) => {
                  const m = displayHistory[idx];
                  if (!m) return null;
                  const x = getChartX(idx, displayHistory.length);
                  const anchor = tickPos === 0 ? 'start' : tickPos === n - 1 ? 'end' : 'middle';
                  return (
                    <g key={`x-lbl-${idx}`}>
                      <line x1={x} y1={chartHeight - chartPadding.bottom} x2={x} y2={chartHeight - chartPadding.bottom + 4} stroke="rgba(255,255,255,0.1)" strokeWidth="0.8" />
                      <text x={x} y={chartHeight - chartPadding.bottom + 15} textAnchor={anchor} fill="var(--text-muted)" className="mono" style={{ fontSize: '0.6rem' }}>
                        {formatXLabel(m.date_time)}
                      </text>
                    </g>
                  );
                });
              })()}

              {hoveredPoint && (() => {
                const tw = 120; const th = 35;
                const tx = hoveredPoint.x > chartWidth - tw - 10 ? hoveredPoint.x - tw - 10 : hoveredPoint.x + 10;
                const ty = hoveredPoint.y < th + 10 ? hoveredPoint.y + 15 : hoveredPoint.y - th - 10;
                return (
                  <g style={{ pointerEvents: 'none' }}>
                    <rect x={tx} y={ty} width={tw} height={th} fill="var(--bg-primary)" stroke="var(--border-color)" strokeWidth="1" rx="3" />
                    <text x={tx + 8} y={ty + 13} fill="var(--text-primary)" className="mono" style={{ fontSize: '0.65rem', fontWeight: 'bold' }}>
                      Nivel: {hoveredPoint.height.toFixed(2)}m
                    </text>
                    <text x={tx + 8} y={ty + 25} fill="var(--text-secondary)" style={{ fontSize: '0.55rem' }}>
                      {formatDate(hoveredPoint.timestamp)}
                    </text>
                  </g>
                );
              })()}

              {chartPoints.map((point, idx) => (
                <rect
                  key={`slice-${idx}`}
                  x={point.x - sliceWidth / 2} y={chartPadding.top}
                  width={sliceWidth} height={chartHeight - chartPadding.top - chartPadding.bottom}
                  fill="transparent" style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoveredPoint({ x: point.x, y: point.y, height: displayHistory[idx].value, timestamp: displayHistory[idx].date_time })}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
              ))}
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

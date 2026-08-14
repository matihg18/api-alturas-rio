import React from 'react';

interface DataSource {
  label: string;
  url: string;
}

const SOURCES: DataSource[] = [
  { label: 'Prefectura Naval Argentina', url: 'https://contenidosweb.prefecturanaval.gob.ar/alturas/' },
  { label: 'INA', url: 'https://alerta.ina.gob.ar' },
  { label: 'CARU', url: 'http://www.caru.org.ar' },
  { label: 'Municipalidad de Gualeguaychú', url: 'https://gualeguaychu.gov.ar/alturadelrio' },
  { label: 'SGB — SACE (Brasil)', url: 'https://www.sgb.gov.br/sace' },
];

export function SourcesFooter() {
  const [open, setOpen] = React.useState(false);
  const [popoverPos, setPopoverPos] = React.useState<{ left: number; bottom: number } | null>(null);
  const triggerRef = React.useRef<HTMLSpanElement>(null);
  const popoverRef = React.useRef<HTMLDivElement>(null);
  const closeTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const calcPosition = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setPopoverPos({
      left: rect.left + rect.width / 2,
      bottom: window.innerHeight - rect.top + 8,
    });
  };

  const handleOpen = () => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    calcPosition();
    setOpen(true);
  };

  const handleClose = () => {
    closeTimer.current = setTimeout(() => setOpen(false), 150);
  };

  // Cierra al hacer click fuera (móvil)
  React.useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target as Node) &&
        popoverRef.current && !popoverRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <footer className="sources-footer">
      <span>
        Los datos hidrológicos son recopilados de{' '}
        <span
          ref={triggerRef}
          className={`sources-trigger${open ? ' is-open' : ''}`}
          onMouseEnter={handleOpen}
          onMouseLeave={handleClose}
          onClick={() => (open ? handleClose() : handleOpen())}
          role="button"
          tabIndex={0}
          aria-expanded={open}
          aria-label="Ver fuentes de datos"
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') open ? handleClose() : handleOpen(); }}
        >
          fuentes oficiales
        </span>
        {' '}con fines informativos. La exactitud o vigencia de los datos es responsabilidad de cada organismo fuente.
      </span>

      {/* Popover renderizado fuera del flow del footer para escapar overflow:hidden */}
      {popoverPos && (
        <div
          ref={popoverRef}
          className={`sources-popover${open ? ' is-open' : ''}`}
          style={{
            position: 'fixed',
            left: popoverPos.left,
            bottom: popoverPos.bottom,
            transform: 'translateX(-50%)',
            zIndex: 2000,
          }}
          onMouseEnter={handleOpen}
          onMouseLeave={handleClose}
        >
          <span className="sources-popover__title">Fuentes de datos</span>
          <span className="sources-popover__list">
            {SOURCES.map((s) => (
              <a
                key={s.url}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                {s.label}
              </a>
            ))}
          </span>
        </div>
      )}
    </footer>
  );
}

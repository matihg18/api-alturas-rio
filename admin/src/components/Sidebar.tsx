import { NavLink } from 'react-router-dom';
import { Layers, MapPin, Hash, Sliders, LayoutDashboard } from 'lucide-react';

const NAV = [
  { to: '/stations',    label: 'Estaciones',         icon: Layers },
  { to: '/gauge-points',label: 'Puntos de aforo',    icon: MapPin  },
  { to: '/datum-types', label: 'Ceros de ref.',       icon: Hash    },
  { to: '/offsets',     label: 'Correcciones',        icon: Sliders },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <div className="sidebar__logo-icon">
            <LayoutDashboard size={15} />
          </div>
          <div>
            <div className="sidebar__title">Panel Admin</div>
            <div className="sidebar__subtitle">Monitoreo de Ríos</div>
          </div>
        </div>
      </div>

      <nav className="sidebar__nav">
        <div className="nav-section-label">Gestión</div>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Icon size={15} className="nav-item__icon" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

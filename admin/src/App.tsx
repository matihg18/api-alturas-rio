import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { ToastProvider } from './components/Toast';
import { StationsPage } from './pages/StationsPage';
import { GaugePointsPage } from './pages/GaugePointsPage';
import { DatumTypesPage } from './pages/DatumTypesPage';
import { OffsetsPage } from './pages/OffsetsPage';
import { MeasurementsExportPage } from './pages/MeasurementsExportPage';

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Navigate to="/stations" replace />} />
              <Route path="/stations"            element={<StationsPage />}           />
              <Route path="/gauge-points"         element={<GaugePointsPage />}        />
              <Route path="/datum-types"          element={<DatumTypesPage />}         />
              <Route path="/offsets"              element={<OffsetsPage />}            />
              <Route path="/measurements-export" element={<MeasurementsExportPage />} />
            </Routes>
          </main>
        </div>
      </ToastProvider>
    </BrowserRouter>
  );
}

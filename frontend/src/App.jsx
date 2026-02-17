import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Costs from './pages/Costs';
import DrillDown from './pages/DrillDown';
import Anomalies from './pages/Anomalies';
import Recommendations from './pages/Recommendations';
import Budgets from './pages/Budgets';
import Tags from './pages/Tags';
import SettingsPage from './pages/Settings';
import Reports from './pages/Reports';
import Login from './pages/Login';
import Kubernetes from './pages/Kubernetes';
import Segments from './pages/Segments';
import Dashboards from './pages/Dashboards';
import Integrations from './pages/Integrations';
import CommandPalette from './components/CommandPalette';

function AppRoutes() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--color-bg)' }}>
        <div className="flex flex-col items-center gap-3 animate-fadeIn">
          <div className="w-10 h-10 rounded-lg gradient-brand flex items-center justify-center">
            <span className="text-white text-lg">⚡</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: 'var(--brand-500)' }} />
            <span style={{ color: 'var(--color-text-tertiary)' }} className="text-sm">Loading CloudPulse...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <>
    <CommandPalette />
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="costs" element={<Costs />} />
        <Route path="why" element={<DrillDown />} />
        <Route path="anomalies" element={<Anomalies />} />
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="budgets" element={<Budgets />} />
        <Route path="tags" element={<Tags />} />
        <Route path="kubernetes" element={<Kubernetes />} />
        <Route path="segments" element={<Segments />} />
        <Route path="dashboards" element={<Dashboards />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="reports" element={<Reports />} />
      </Route>
    </Routes>
    </>  
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;

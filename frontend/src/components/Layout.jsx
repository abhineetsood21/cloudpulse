import { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, DollarSign, HelpCircle, AlertTriangle, Lightbulb, Wallet,
  LogOut, Settings, Tag, FileText, ChevronLeft, ChevronRight, Menu, X,
  Moon, Sun, Search, Bell, Container, GitBranch, BarChart3, Plug,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const navSections = [
  {
    label: 'Overview',
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/costs', icon: DollarSign, label: 'Cost Explorer' },
      { to: '/why', icon: HelpCircle, label: 'Why?' },
    ],
  },
  {
    label: 'Management',
    items: [
      { to: '/budgets', icon: Wallet, label: 'Budgets' },
      { to: '/segments', icon: GitBranch, label: 'Segments' },
      { to: '/kubernetes', icon: Container, label: 'Kubernetes' },
      { to: '/tags', icon: Tag, label: 'Tag Breakdown' },
      { to: '/reports', icon: FileText, label: 'Reports' },
    ],
  },
  {
    label: 'Monitoring',
    items: [
      { to: '/anomalies', icon: AlertTriangle, label: 'Anomalies' },
      { to: '/recommendations', icon: Lightbulb, label: 'Recommendations' },
    ],
  },
  {
    label: 'Connect',
    items: [
      { to: '/integrations', icon: Plug, label: 'Integrations' },
    ],
  },
];

const pageTitles = {
  '/': 'Dashboard',
  '/costs': 'Cost Explorer',
  '/why': 'Why?',
  '/budgets': 'Budgets',
  '/segments': 'Segments',
  '/kubernetes': 'Kubernetes',
  '/tags': 'Tag Breakdown',
  '/reports': 'Reports',
  '/anomalies': 'Anomalies',
  '/recommendations': 'Recommendations',
  '/integrations': 'Integrations',
  '/settings': 'Settings',
};

export default function Layout() {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true');
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem('sidebar_collapsed', collapsed);
  }, [collapsed]);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const currentPageTitle = pageTitles[location.pathname] || 'CloudPulse';
  const userInitials = user?.email?.slice(0, 2).toUpperCase() || '??';

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: 'var(--color-bg)' }}>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          style={{ animation: 'overlayIn 0.2s ease-out' }}
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:relative z-50 h-full flex flex-col transition-all duration-300 ease-in-out
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{
          width: collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
          backgroundColor: 'var(--sidebar-bg)',
          borderRight: '1px solid var(--sidebar-border)',
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center gap-3 px-5 h-16 flex-shrink-0"
          style={{ borderBottom: '1px solid var(--sidebar-border)' }}
        >
          <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm font-bold">⚡</span>
          </div>
          {!collapsed && (
            <div className="animate-fadeIn">
              <span className="text-white font-bold text-base tracking-tight">CloudPulse</span>
              <span
                className="block text-[10px] font-medium tracking-wider uppercase"
                style={{ color: 'var(--sidebar-text)' }}
              >
                Cloud Cost Intelligence
              </span>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
          {navSections.map((section) => (
            <div key={section.label}>
              {!collapsed && (
                <p
                  className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider"
                  style={{ color: 'var(--sidebar-text)', opacity: 0.6 }}
                >
                  {section.label}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-all duration-150
                      ${isActive
                        ? 'text-white'
                        : 'hover:bg-[var(--sidebar-hover)]'
                      }
                      ${collapsed ? 'justify-center' : ''}
                      `
                    }
                    style={({ isActive }) =>
                      isActive
                        ? { backgroundColor: 'var(--sidebar-accent)', color: 'var(--sidebar-text-active)' }
                        : { color: 'var(--sidebar-text)' }
                    }
                    title={collapsed ? label : undefined}
                  >
                    <Icon size={18} className="flex-shrink-0" />
                    {!collapsed && <span>{label}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar footer */}
        <div className="flex-shrink-0 px-3 py-3" style={{ borderTop: '1px solid var(--sidebar-border)' }}>
          {/* Settings link */}
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm font-medium transition-all duration-150
              ${isActive ? 'text-white' : 'hover:bg-[var(--sidebar-hover)]'}
              ${collapsed ? 'justify-center' : ''}`
            }
            style={({ isActive }) =>
              isActive
                ? { backgroundColor: 'var(--sidebar-accent)', color: 'var(--sidebar-text-active)' }
                : { color: 'var(--sidebar-text)' }
            }
            title={collapsed ? 'Settings' : undefined}
          >
            <Settings size={18} className="flex-shrink-0" />
            {!collapsed && <span>Settings</span>}
          </NavLink>

          {/* Collapse toggle (desktop only) */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex items-center gap-3 px-3 py-2.5 w-full rounded-[var(--radius-md)] text-sm transition-all duration-150 hover:bg-[var(--sidebar-hover)]"
            style={{ color: 'var(--sidebar-text)' }}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            {!collapsed && <span className="text-xs">Collapse</span>}
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top header bar */}
        <header
          className="h-16 flex items-center justify-between px-4 lg:px-8 flex-shrink-0"
          style={{
            backgroundColor: 'var(--color-surface)',
            borderBottom: '1px solid var(--color-border)',
          }}
        >
          <div className="flex items-center gap-4">
            {/* Mobile menu button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-[var(--radius-sm)] transition-colors"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>

            <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              {currentPageTitle}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            {/* Search trigger */}
            <button
              className="hidden md:flex items-center gap-2 px-3 py-1.5 text-sm rounded-[var(--radius-md)] transition-colors"
              style={{
                backgroundColor: 'var(--color-surface-secondary)',
                color: 'var(--color-text-tertiary)',
                border: '1px solid var(--color-border)',
              }}
              onClick={() => window.dispatchEvent(new CustomEvent('open-command-palette'))}
            >
              <Search size={14} />
              <span>Search...</span>
              <kbd
                className="ml-4 px-1.5 py-0.5 text-[10px] font-semibold rounded"
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-tertiary)',
                }}
              >
                ⌘K
              </kbd>
            </button>

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)]"
              style={{ color: 'var(--color-text-secondary)' }}
              title={isDark ? 'Light mode' : 'Dark mode'}
            >
              {isDark ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            {/* Notifications */}
            <button
              className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)] relative"
              style={{ color: 'var(--color-text-secondary)' }}
              onClick={() => window.dispatchEvent(new CustomEvent('toggle-notifications'))}
            >
              <Bell size={18} />
            </button>

            {/* User menu */}
            <div className="flex items-center gap-3 ml-2 pl-4" style={{ borderLeft: '1px solid var(--color-border)' }}>
              <div className="hidden md:block text-right">
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
                  {user?.email?.split('@')[0] || 'User'}
                </p>
                <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                  Free Plan
                </p>
              </div>
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                style={{ background: 'var(--brand-600)' }}
              >
                {userInitials}
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)]"
                style={{ color: 'var(--color-text-tertiary)' }}
                title="Sign out"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-auto" style={{ backgroundColor: 'var(--color-bg)' }}>
          <div className="p-4 lg:p-8 max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

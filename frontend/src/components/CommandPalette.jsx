import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, DollarSign, HelpCircle, AlertTriangle, Lightbulb, Wallet,
  Settings, Tag, FileText, Search, Moon, Sun,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const commands = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/', section: 'Pages' },
  { id: 'costs', label: 'Cost Explorer', icon: DollarSign, path: '/costs', section: 'Pages' },
  { id: 'why', label: 'Why? Drill-Down', icon: HelpCircle, path: '/why', section: 'Pages' },
  { id: 'budgets', label: 'Budgets', icon: Wallet, path: '/budgets', section: 'Pages' },
  { id: 'tags', label: 'Tag Breakdown', icon: Tag, path: '/tags', section: 'Pages' },
  { id: 'reports', label: 'Reports', icon: FileText, path: '/reports', section: 'Pages' },
  { id: 'anomalies', label: 'Anomalies', icon: AlertTriangle, path: '/anomalies', section: 'Pages' },
  { id: 'recommendations', label: 'Recommendations', icon: Lightbulb, path: '/recommendations', section: 'Pages' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings', section: 'Pages' },
  { id: 'toggle-theme', label: 'Toggle Dark Mode', icon: Moon, action: 'toggle-theme', section: 'Actions' },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const { toggleTheme, isDark } = useTheme();

  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((o) => !o);
      }
    }
    function handleCustomEvent() {
      setOpen(true);
    }
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('open-command-palette', handleCustomEvent);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('open-command-palette', handleCustomEvent);
    };
  }, []);

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const filtered = commands.filter((c) =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  function execute(cmd) {
    setOpen(false);
    if (cmd.path) {
      navigate(cmd.path);
    } else if (cmd.action === 'toggle-theme') {
      toggleTheme();
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) execute(filtered[selectedIndex]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  if (!open) return null;

  const sections = [...new Set(filtered.map((c) => c.section))];

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center pt-[20vh]" style={{ animation: 'overlayIn 0.15s ease-out' }}>
      <div className="absolute inset-0 glass" style={{ backgroundColor: 'rgba(0,0,0,0.4)' }} onClick={() => setOpen(false)} />
      <div
        className="relative w-full max-w-lg rounded-[var(--radius-xl)] overflow-hidden"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-xl)',
          border: '1px solid var(--color-border)',
          animation: 'modalIn 0.2s ease-out',
        }}
      >
        <div className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <Search size={18} style={{ color: 'var(--color-text-tertiary)' }} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search pages and actions..."
            className="flex-1 bg-transparent outline-none text-sm"
            style={{ color: 'var(--color-text-primary)' }}
          />
          <kbd
            className="px-1.5 py-0.5 text-[10px] font-semibold rounded"
            style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-tertiary)' }}
          >
            ESC
          </kbd>
        </div>
        <div className="max-h-72 overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-center py-6" style={{ color: 'var(--color-text-tertiary)' }}>No results found</p>
          ) : (
            sections.map((section) => (
              <div key={section}>
                <p className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>
                  {section}
                </p>
                {filtered.filter((c) => c.section === section).map((cmd) => {
                  const globalIdx = filtered.indexOf(cmd);
                  const Icon = cmd.action === 'toggle-theme' ? (isDark ? Sun : Moon) : cmd.icon;
                  return (
                    <button
                      key={cmd.id}
                      onClick={() => execute(cmd)}
                      onMouseEnter={() => setSelectedIndex(globalIdx)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm transition-colors"
                      style={{
                        backgroundColor: selectedIndex === globalIdx ? 'var(--color-surface-secondary)' : 'transparent',
                        color: selectedIndex === globalIdx ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                      }}
                    >
                      <Icon size={16} style={{ color: selectedIndex === globalIdx ? 'var(--brand-500)' : 'var(--color-text-tertiary)' }} />
                      <span className="flex-1 text-left">{cmd.label}</span>
                      {cmd.path && (
                        <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Go to</span>
                      )}
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

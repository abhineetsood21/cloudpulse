import { useState, useEffect } from 'react';
import {
  LayoutGrid, Plus, Trash2, Edit3, Copy, Star, BarChart3,
  DollarSign, AlertTriangle, Wallet, TrendingUp, TrendingDown,
  Server, Clock, Eye,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/EmptyState';
import { StatCard } from '../components/ui/StatCard';
import { Skeleton } from '../components/ui/Skeleton';

const WIDGET_TYPES = [
  { id: 'cost_summary', label: 'Cost Summary', icon: DollarSign, description: 'Total spend with trend' },
  { id: 'top_services', label: 'Top Services', icon: BarChart3, description: 'Highest cost services' },
  { id: 'budget_status', label: 'Budget Status', icon: Wallet, description: 'Budget utilization' },
  { id: 'anomaly_count', label: 'Anomaly Count', icon: AlertTriangle, description: 'Active anomalies' },
  { id: 'savings_opportunities', label: 'Savings', icon: TrendingDown, description: 'Potential savings' },
  { id: 'resource_count', label: 'Resource Count', icon: Server, description: 'Active resources' },
  { id: 'forecast', label: 'Forecast', icon: TrendingUp, description: 'Month-end projection' },
  { id: 'recent_activity', label: 'Recent Activity', icon: Clock, description: 'Latest cost events' },
];

const DEFAULT_DASHBOARDS = [
  {
    id: 'default',
    name: 'Executive Overview',
    description: 'High-level cost metrics for leadership',
    isDefault: true,
    widgets: ['cost_summary', 'forecast', 'budget_status', 'savings_opportunities', 'top_services', 'anomaly_count'],
    createdAt: '2025-01-15',
  },
];

function WidgetCard({ type }) {
  const config = WIDGET_TYPES.find((w) => w.id === type);
  if (!config) return null;
  const Icon = config.icon;

  const mockValues = {
    cost_summary: { value: '$4,285.30', sub: '+12.3% vs last month' },
    top_services: { value: 'EC2, RDS, S3', sub: '78% of total spend' },
    budget_status: { value: '72% Used', sub: '$3,085 of $4,250 budget' },
    anomaly_count: { value: '3 Active', sub: '2 high severity' },
    savings_opportunities: { value: '$892/mo', sub: '14 recommendations' },
    resource_count: { value: '247', sub: 'across 3 regions' },
    forecast: { value: '$5,120', sub: 'Projected month-end' },
    recent_activity: { value: '12 Events', sub: 'Last 24 hours' },
  };

  const mock = mockValues[type] || { value: '-', sub: '' };

  return (
    <div
      className="rounded-[var(--radius-lg)] p-5 transition-all duration-200 hover:shadow-[var(--shadow-md)]"
      style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className="p-2 rounded-[var(--radius-md)]" style={{ background: 'var(--brand-50)', color: 'var(--brand-600)' }}>
          <Icon size={16} />
        </div>
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>{config.label}</span>
      </div>
      <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>{mock.value}</p>
      <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>{mock.sub}</p>
    </div>
  );
}

export default function Dashboards() {
  const [dashboards, setDashboards] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('cp_dashboards') || 'null');
      return saved || DEFAULT_DASHBOARDS;
    } catch { return DEFAULT_DASHBOARDS; }
  });
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(null);
  const [viewDashboard, setViewDashboard] = useState(null);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [selectedWidgets, setSelectedWidgets] = useState([]);

  useEffect(() => {
    localStorage.setItem('cp_dashboards', JSON.stringify(dashboards));
  }, [dashboards]);

  function createDashboard() {
    const dashboard = {
      id: Date.now().toString(),
      name: newName || 'Untitled Dashboard',
      description: newDescription,
      isDefault: false,
      widgets: selectedWidgets,
      createdAt: new Date().toISOString().split('T')[0],
    };
    setDashboards([...dashboards, dashboard]);
    setShowCreate(false);
    resetForm();
  }

  function deleteDashboard(id) {
    setDashboards(dashboards.filter((d) => d.id !== id));
    if (viewDashboard?.id === id) setViewDashboard(null);
  }

  function duplicateDashboard(d) {
    const copy = { ...d, id: Date.now().toString(), name: `${d.name} (Copy)`, isDefault: false };
    setDashboards([...dashboards, copy]);
  }

  function setDefault(id) {
    setDashboards(dashboards.map((d) => ({ ...d, isDefault: d.id === id })));
  }

  function toggleWidget(widgetId) {
    setSelectedWidgets((prev) =>
      prev.includes(widgetId) ? prev.filter((w) => w !== widgetId) : [...prev, widgetId]
    );
  }

  function resetForm() {
    setNewName(''); setNewDescription(''); setSelectedWidgets([]);
  }

  // Dashboard detail view
  if (viewDashboard) {
    const db = dashboards.find((d) => d.id === viewDashboard.id) || viewDashboard;
    return (
      <div className="animate-fadeIn">
        <PageHeader title={db.name} description={db.description || 'Custom dashboard'} icon={LayoutGrid}>
          <Button variant="ghost" size="sm" onClick={() => setViewDashboard(null)}>← Back</Button>
          {db.isDefault && <Badge variant="brand">Default</Badge>}
        </PageHeader>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {db.widgets.map((w, i) => (
            <div key={i} className="animate-fadeInUp" style={{ animationDelay: `${i * 50}ms` }}>
              <WidgetCard type={w} />
            </div>
          ))}
        </div>
        {db.widgets.length === 0 && (
          <EmptyState icon={LayoutGrid} title="No widgets" description="Edit this dashboard to add widgets." />
        )}
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Dashboards" description="Create custom dashboards with the widgets you need" icon={LayoutGrid}>
        <Button size="sm" icon={Plus} onClick={() => setShowCreate(true)}>New Dashboard</Button>
      </PageHeader>

      {dashboards.length === 0 ? (
        <EmptyState icon={LayoutGrid} title="No dashboards" description="Create your first dashboard to get a custom view of your cloud costs." actionLabel="Create Dashboard" actionIcon={Plus} onAction={() => setShowCreate(true)} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((db, i) => (
            <Card key={db.id} hover className="animate-fadeInUp" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-[var(--radius-md)]" style={{ background: 'var(--brand-50)', color: 'var(--brand-600)' }}>
                    <LayoutGrid size={16} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>{db.name}</h3>
                    {db.isDefault && <Badge variant="brand" size="sm">Default</Badge>}
                  </div>
                </div>
              </div>
              {db.description && (
                <p className="text-xs mb-3" style={{ color: 'var(--color-text-secondary)' }}>{db.description}</p>
              )}
              <div className="flex flex-wrap gap-1 mb-4">
                {db.widgets.slice(0, 4).map((w) => {
                  const cfg = WIDGET_TYPES.find((wt) => wt.id === w);
                  return cfg ? <Badge key={w} variant="neutral" size="sm">{cfg.label}</Badge> : null;
                })}
                {db.widgets.length > 4 && <Badge variant="neutral" size="sm">+{db.widgets.length - 4}</Badge>}
              </div>
              <div className="flex items-center gap-1 pt-3" style={{ borderTop: '1px solid var(--color-border-light)' }}>
                <Button variant="ghost" size="sm" icon={Eye} onClick={() => setViewDashboard(db)}>View</Button>
                <Button variant="ghost" size="sm" icon={Copy} onClick={() => duplicateDashboard(db)} />
                {!db.isDefault && <Button variant="ghost" size="sm" icon={Star} onClick={() => setDefault(db.id)} />}
                {db.id !== 'default' && <Button variant="ghost" size="sm" icon={Trash2} onClick={() => deleteDashboard(db.id)} />}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Dashboard Modal */}
      <Modal open={showCreate} onClose={() => { setShowCreate(false); resetForm(); }} title="Create Dashboard" size="lg">
        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Name</label>
            <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g., Engineering Team View" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} autoFocus />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Description</label>
            <input value={newDescription} onChange={(e) => setNewDescription(e.target.value)} placeholder="Optional description" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-primary)' }}>Widgets</label>
            <div className="grid grid-cols-2 gap-2">
              {WIDGET_TYPES.map(({ id, label, icon: Icon, description }) => (
                <button
                  key={id}
                  onClick={() => toggleWidget(id)}
                  className="flex items-center gap-3 p-3 rounded-[var(--radius-md)] text-left transition-all"
                  style={{
                    border: selectedWidgets.includes(id) ? '2px solid var(--brand-500)' : '1px solid var(--color-border)',
                    backgroundColor: selectedWidgets.includes(id) ? 'var(--brand-50)' : 'var(--color-surface)',
                  }}
                >
                  <Icon size={18} style={{ color: selectedWidgets.includes(id) ? 'var(--brand-600)' : 'var(--color-text-tertiary)' }} />
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={() => { setShowCreate(false); resetForm(); }}>Cancel</Button>
            <Button size="sm" onClick={createDashboard}>Create Dashboard</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

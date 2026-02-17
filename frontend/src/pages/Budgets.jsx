import { useEffect, useState, useMemo } from 'react';
import { Wallet, Plus, RefreshCw, Trash2, AlertTriangle, CheckCircle, TrendingUp, Target } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Line, ComposedChart } from 'recharts';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/EmptyState';
import { SkeletonCard, Skeleton } from '../components/ui/Skeleton';
import { StatCard } from '../components/ui/StatCard';

function BudgetStatusBadge({ pctUsed, alertAtPct }) {
  if (pctUsed >= 1.0) return <Badge variant="error" icon={AlertTriangle}>Over Budget</Badge>;
  if (pctUsed >= alertAtPct) return <Badge variant="warning" icon={AlertTriangle}>Warning</Badge>;
  return <Badge variant="success" icon={CheckCircle}>On Track</Badge>;
}

function ProgressBar({ pctUsed, alertAtPct }) {
  const pct = Math.min(pctUsed * 100, 100);
  let color = 'var(--color-success)';
  if (pctUsed >= 1.0) color = 'var(--color-error)';
  else if (pctUsed >= alertAtPct) color = 'var(--color-warning)';

  return (
    <div className="w-full h-2.5 rounded-full overflow-hidden relative" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
      <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${pct}%`, backgroundColor: color }} />
      <div className="absolute top-0 h-full w-0.5" style={{ left: `${alertAtPct * 100}%`, backgroundColor: 'var(--color-text-tertiary)', opacity: 0.5 }} />
    </div>
  );
}

function generatePerformanceData(budget) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  return months.map((month, i) => {
    const base = budget.amount * (0.6 + Math.random() * 0.5);
    return {
      month,
      actual: Math.round(base * 100) / 100,
      budget: budget.amount,
      forecast: i === months.length - 1 ? Math.round(base * 1.12 * 100) / 100 : null,
    };
  });
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-lg)' }}>
      <p className="font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
      {payload.filter(e => e.value != null).map((entry, i) => (
        <p key={i} style={{ color: entry.color }}>{entry.name}: ${entry.value?.toFixed(2)}</p>
      ))}
    </div>
  );
};

export default function Budgets() {
  const [budgets, setBudgets] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState(null);
  const [viewMode, setViewMode] = useState('cards');
  const [formData, setFormData] = useState({
    name: '', amount: '', period: 'monthly', service_filter: '', alert_at_pct: 0.80,
  });

  const accountId = accounts[0]?.id;

  async function loadData() {
    try {
      const accts = await api.getAccounts();
      setAccounts(accts);
      if (accts.length > 0) {
        const budgetData = await api.getBudgets(accts[0].id);
        setBudgets(budgetData);
      }
    } catch (err) { console.error(err); } finally { setLoading(false); }
  }

  useEffect(() => { loadData(); }, []);

  const stats = useMemo(() => {
    const total = budgets.reduce((s, b) => s + b.amount, 0);
    const spent = budgets.reduce((s, b) => s + b.current_spend, 0);
    const overBudget = budgets.filter(b => b.current_spend > b.amount).length;
    const atRisk = budgets.filter(b => { const p = b.amount > 0 ? b.current_spend / b.amount : 0; return p >= b.alert_at_pct && p < 1; }).length;
    return { total, spent, overBudget, atRisk, remaining: Math.max(total - spent, 0) };
  }, [budgets]);

  async function handleCreate(e) {
    e.preventDefault();
    if (!accountId) return;
    try {
      await api.createBudget(accountId, { name: formData.name, amount: parseFloat(formData.amount), period: formData.period, service_filter: formData.service_filter || null, alert_at_pct: formData.alert_at_pct });
      setShowForm(false);
      setFormData({ name: '', amount: '', period: 'monthly', service_filter: '', alert_at_pct: 0.80 });
      await loadData();
    } catch (err) { console.error(err); }
  }

  async function handleDelete(budgetId) {
    try {
      await api.deleteBudget(budgetId);
      setBudgets(budgets.filter((b) => b.id !== budgetId));
      if (selectedBudget?.id === budgetId) setSelectedBudget(null);
    } catch (err) { console.error(err); }
  }

  async function handleRefresh() {
    if (!accountId) return;
    setRefreshing(true);
    try { const updated = await api.checkBudgets(accountId); setBudgets(updated); } catch (err) { console.error(err); } finally { setRefreshing(false); }
  }

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="flex items-center justify-between mb-8">
          <div><Skeleton variant="text" className="w-32 h-7 mb-2" /><Skeleton variant="text" className="w-64 h-4" /></div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger-children"><SkeletonCard /><SkeletonCard /></div>
      </div>
    );
  }

  const performanceData = selectedBudget ? generatePerformanceData(selectedBudget) : [];

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Budgets" description="Set spending limits and track budget performance across periods" icon={Wallet}>
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {['cards', 'performance'].map(v => (
            <button key={v} onClick={() => setViewMode(v)}
              className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all capitalize"
              style={{ backgroundColor: viewMode === v ? 'var(--brand-600)' : 'transparent', color: viewMode === v ? 'white' : 'var(--color-text-secondary)' }}>
              {v}
            </button>
          ))}
        </div>
        <Button variant="secondary" size="sm" icon={RefreshCw} onClick={handleRefresh} loading={refreshing}>Refresh</Button>
        <Button size="sm" icon={Plus} onClick={() => setShowForm(true)}>New Budget</Button>
      </PageHeader>

      {budgets.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Budgeted" value={`$${stats.total.toFixed(0)}`} icon={Target} />
          <StatCard label="Total Spent" value={`$${stats.spent.toFixed(0)}`} icon={TrendingUp} trend={stats.spent > stats.total ? 'up' : 'down'} trendValue={`${((stats.spent / Math.max(stats.total, 1)) * 100).toFixed(0)}% used`} />
          <StatCard label="Remaining" value={`$${stats.remaining.toFixed(0)}`} icon={Wallet} />
          <StatCard label="At Risk / Over" value={`${stats.atRisk} / ${stats.overBudget}`} icon={AlertTriangle} trend={stats.overBudget > 0 ? 'up' : 'neutral'} trendValue={stats.overBudget > 0 ? 'Action needed' : 'All clear'} />
        </div>
      )}

      <Modal open={showForm} onClose={() => setShowForm(false)} title="Create Budget">
        <form onSubmit={handleCreate}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Name</label>
              <input type="text" required value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Monthly Total" className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm outline-none"
                style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Amount (USD)</label>
              <input type="number" required min="1" step="0.01" value={formData.amount} onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                placeholder="100.00" className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm outline-none"
                style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Period</label>
              <select value={formData.period} onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm outline-none"
                style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }}>
                <option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Service (optional)</label>
              <input type="text" value={formData.service_filter} onChange={(e) => setFormData({ ...formData, service_filter: e.target.value })}
                placeholder="All services" className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm outline-none"
                style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Alert at ({(formData.alert_at_pct * 100).toFixed(0)}%)</label>
              <input type="range" min="0.1" max="1.0" step="0.05" value={formData.alert_at_pct}
                onChange={(e) => setFormData({ ...formData, alert_at_pct: parseFloat(e.target.value) })} className="w-full accent-[var(--brand-600)]" />
            </div>
          </div>
          <div className="flex gap-2 mt-6 justify-end">
            <Button variant="secondary" type="button" onClick={() => setShowForm(false)}>Cancel</Button>
            <Button type="submit">Create Budget</Button>
          </div>
        </form>
      </Modal>

      <Modal open={!!selectedBudget} onClose={() => setSelectedBudget(null)} title={selectedBudget?.name || 'Budget Performance'}>
        {selectedBudget && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              {[{ label: 'Budget', value: `$${selectedBudget.amount.toFixed(0)}`, color: 'var(--color-text-primary)' },
                { label: 'Spent', value: `$${selectedBudget.current_spend.toFixed(0)}`, color: 'var(--color-text-primary)' },
                { label: 'Forecast', value: `$${(selectedBudget.current_spend * 1.1).toFixed(0)}`, color: selectedBudget.current_spend > selectedBudget.amount ? 'var(--color-error)' : 'var(--brand-600)' },
              ].map(s => (
                <div key={s.label} className="p-3 rounded-[var(--radius-md)] text-center" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{s.label}</p>
                  <p className="text-lg font-bold" style={{ color: s.color }}>{s.value}</p>
                </div>
              ))}
            </div>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={selectedBudget.amount} stroke="var(--color-error)" strokeDasharray="5 5" label={{ value: 'Budget', position: 'right', fontSize: 10, fill: 'var(--color-error)' }} />
                  <Bar dataKey="actual" fill="var(--brand-500)" radius={[4, 4, 0, 0]} name="Actual" />
                  <Line dataKey="forecast" stroke="var(--color-warning)" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Forecast" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </Modal>

      {budgets.length === 0 ? (
        <EmptyState icon={Wallet} title="No budgets yet" description="Create a budget to start tracking your spending limits and get alerted before you go over."
          actionLabel="Create Budget" actionIcon={Plus} onAction={() => setShowForm(true)} />
      ) : viewMode === 'performance' ? (
        <Card>
          <CardTitle>Budget Performance Overview</CardTitle>
          <div style={{ height: 350 }} className="mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={budgets.map(b => ({ name: b.name, spent: b.current_spend, budget: b.amount }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="spent" fill="var(--brand-500)" name="Spent" radius={[4, 4, 0, 0]} />
                <Bar dataKey="budget" fill="var(--color-border)" name="Budget Limit" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger-children">
          {budgets.map((budget) => {
            const pctUsed = budget.amount > 0 ? budget.current_spend / budget.amount : 0;
            return (
              <Card key={budget.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setSelectedBudget(budget)}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{budget.name}</h3>
                    <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{budget.period} · {budget.service_filter || 'All services'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <BudgetStatusBadge pctUsed={pctUsed} alertAtPct={budget.alert_at_pct} />
                    <button onClick={(e) => { e.stopPropagation(); handleDelete(budget.id); }}
                      className="p-1.5 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-error-bg)]"
                      style={{ color: 'var(--color-text-tertiary)' }}><Trash2 size={14} /></button>
                  </div>
                </div>
                <div className="mb-2">
                  <div className="flex justify-between text-sm mb-1.5">
                    <span style={{ color: 'var(--color-text-secondary)' }}>${budget.current_spend.toFixed(2)} of ${budget.amount.toFixed(2)}</span>
                    <span className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{(pctUsed * 100).toFixed(0)}%</span>
                  </div>
                  <ProgressBar pctUsed={pctUsed} alertAtPct={budget.alert_at_pct} />
                </div>
                <div className="flex items-center gap-2 mt-3 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                  <TrendingUp size={12} /><span>Forecast: ${(budget.current_spend * 1.1).toFixed(2)}</span>
                  <span className="ml-auto">Remaining: ${Math.max(budget.amount - budget.current_spend, 0).toFixed(2)}</span>
                </div>
                {budget.last_checked_at && (
                  <p className="text-xs mt-2" style={{ color: 'var(--color-text-tertiary)' }}>Updated: {new Date(budget.last_checked_at).toLocaleDateString()}</p>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

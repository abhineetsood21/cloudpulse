import { useEffect, useState, useMemo } from 'react';
import {
  XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area,
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, Legend,
  CartesianGrid,
} from 'recharts';
import {
  DollarSign, Download, BarChart3, LineChart as LineChartIcon,
  PieChart as PieChartIcon, AreaChart as AreaChartIcon,
  Layers, X, Save, Bookmark,
} from 'lucide-react';
import { api } from '../api/client';
import { Card, CardTitle, CardHeader } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { SkeletonChart, SkeletonTable, Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Modal } from '../components/ui/Modal';

const CHART_COLORS = [
  'var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)',
  'var(--chart-5)', 'var(--chart-6)', 'var(--chart-7)', 'var(--chart-8)',
];

const chartTooltipStyle = {
  backgroundColor: 'var(--color-surface-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-md)',
  color: 'var(--color-text-primary)',
};

const CHART_TYPES = [
  { id: 'area', label: 'Area', icon: AreaChartIcon },
  { id: 'bar', label: 'Stacked Bar', icon: BarChart3 },
  { id: 'line', label: 'Line', icon: LineChartIcon },
  { id: 'pie', label: 'Pie', icon: PieChartIcon },
];

const DATE_BINS = [
  { id: 'daily', label: 'Daily' },
  { id: 'weekly', label: 'Weekly' },
  { id: 'monthly', label: 'Monthly' },
];

const GROUP_BY_OPTIONS = [
  { id: 'none', label: 'No Grouping' },
  { id: 'service', label: 'Service' },
  { id: 'region', label: 'Region' },
  { id: 'account', label: 'Account' },
];

function CostsSkeleton() {
  return (
    <div className="animate-fadeIn">
      <div className="flex items-center justify-between mb-8">
        <div><Skeleton variant="text" className="w-40 h-7 mb-2" /><Skeleton variant="text" className="w-56 h-4" /></div>
      </div>
      <div className="flex gap-2 mb-6">
        <Skeleton className="w-24 h-9" /><Skeleton className="w-24 h-9" /><Skeleton className="w-24 h-9" /><Skeleton className="w-24 h-9" />
      </div>
      <Skeleton className="w-full h-28 mb-6" />
      <SkeletonChart className="mb-6" />
      <SkeletonTable rows={6} cols={4} />
    </div>
  );
}

function aggregateByBin(dailyData, bin) {
  if (bin === 'daily' || !dailyData.length) return dailyData;
  const groups = {};
  dailyData.forEach((d) => {
    const dateObj = new Date(d.fullDate || d.date);
    let key;
    if (bin === 'weekly') {
      const startOfWeek = new Date(dateObj);
      startOfWeek.setDate(dateObj.getDate() - dateObj.getDay());
      key = startOfWeek.toISOString().split('T')[0];
    } else {
      key = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
    }
    if (!groups[key]) groups[key] = { date: key, amount: 0, services: {} };
    groups[key].amount += d.amount;
    if (d.services) {
      Object.entries(d.services).forEach(([svc, amt]) => {
        groups[key].services[svc] = (groups[key].services[svc] || 0) + amt;
      });
    }
  });
  return Object.values(groups).sort((a, b) => a.date.localeCompare(b.date));
}

function makeCumulative(data) {
  let running = 0;
  return data.map((d) => {
    running += d.amount;
    return { ...d, amount: Math.round(running * 100) / 100 };
  });
}

export default function Costs() {
  const [costs, setCosts] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [chartType, setChartType] = useState('area');
  const [dateBin, setDateBin] = useState('daily');
  const [groupBy, setGroupBy] = useState('service');
  const [cumulative, setCumulative] = useState(false);
  const [savedFilters, setSavedFilters] = useState(() => {
    try { return JSON.parse(localStorage.getItem('cp_saved_filters') || '[]'); } catch { return []; }
  });
  const [showSaveFilter, setShowSaveFilter] = useState(false);
  const [filterName, setFilterName] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const accountsData = await api.getAccounts();
        setAccounts(accountsData);
        if (accountsData.length > 0) {
          const end = new Date().toISOString().split('T')[0];
          const start = new Date(Date.now() - days * 86400000).toISOString().split('T')[0];
          const costsData = await api.getCosts(accountsData[0].id, start, end);
          setCosts(costsData);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [days]);

  const dailyDataRaw = useMemo(() => {
    if (!costs) return [];
    return costs.daily_totals.map((d) => {
      const entry = { date: d.date.slice(5), fullDate: d.date, amount: d.amount, services: {} };
      costs.by_service.forEach((svc) => {
        entry.services[svc.service] = svc.amount / (costs.daily_totals.length || 1);
      });
      return entry;
    });
  }, [costs]);

  const chartData = useMemo(() => {
    let data = aggregateByBin(dailyDataRaw, dateBin);
    if (cumulative) data = makeCumulative(data);
    return data;
  }, [dailyDataRaw, dateBin, cumulative]);

  const topServices = useMemo(() => {
    if (!costs) return [];
    return costs.by_service.slice(0, 8).map((s) => s.service);
  }, [costs]);

  const pieData = useMemo(() => {
    if (!costs) return [];
    return costs.by_service.map((s) => ({ name: s.service, value: s.amount }));
  }, [costs]);

  function saveCurrentFilter() {
    const filter = { id: Date.now(), name: filterName || `Filter ${savedFilters.length + 1}`, days, chartType, dateBin, groupBy, cumulative };
    const next = [...savedFilters, filter];
    setSavedFilters(next);
    localStorage.setItem('cp_saved_filters', JSON.stringify(next));
    setShowSaveFilter(false);
    setFilterName('');
  }

  function loadFilter(f) {
    setDays(f.days); setChartType(f.chartType); setDateBin(f.dateBin); setGroupBy(f.groupBy); setCumulative(f.cumulative);
    setShowFilters(false);
  }

  function deleteFilter(id) {
    const next = savedFilters.filter((f) => f.id !== id);
    setSavedFilters(next);
    localStorage.setItem('cp_saved_filters', JSON.stringify(next));
  }

  function exportCSV() {
    const headers = 'Service,Amount,Percent,AvgPerDay\n';
    const rows = costs.by_service.map((svc) => {
      const pct = costs.total_spend > 0 ? ((svc.amount / costs.total_spend) * 100).toFixed(1) : '0';
      const avg = (svc.amount / (costs.daily_totals.length || 1)).toFixed(2);
      return `"${svc.service}",${svc.amount.toFixed(2)},${pct},${avg}`;
    }).join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `cloudpulse-costs-${days}d.csv`; a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <CostsSkeleton />;
  if (!costs) return <EmptyState icon={DollarSign} title="No provider connected" description="Connect a cloud or SaaS provider to view cost data." actionLabel="Connect a Provider" onAction={() => window.location.href = '/integrations'} />;

  const avgDay = costs.total_spend / (costs.daily_totals.length || 1);

  const renderChart = () => {
    if (chartType === 'pie') {
      return (
        <ResponsiveContainer width="100%" height={350}>
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={130} innerRadius={60} paddingAngle={2} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={{ stroke: 'var(--color-text-tertiary)' }}>
              {pieData.map((_, i) => (<Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />))}
            </Pie>
            <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${v.toFixed(2)}`, 'Cost']} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );
    }
    if (chartType === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} tickFormatter={(v) => `$${v}`} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${Number(v).toFixed(2)}`]} />
            {groupBy === 'service' && topServices.length > 0 ? (
              topServices.map((svc, i) => (
                <Bar key={svc} dataKey={`services.${svc}`} name={svc} stackId="a" fill={CHART_COLORS[i % CHART_COLORS.length]} radius={i === topServices.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]} />
              ))
            ) : (
              <Bar dataKey="amount" name="Cost" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
            )}
          </BarChart>
        </ResponsiveContainer>
      );
    }
    if (chartType === 'line') {
      return (
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} tickFormatter={(v) => `$${v}`} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${Number(v).toFixed(2)}`]} />
            <Line type="monotone" dataKey="amount" name="Cost" stroke="var(--chart-1)" strokeWidth={2.5} dot={{ r: 3, fill: 'var(--chart-1)' }} activeDot={{ r: 5 }} />
          </LineChart>
        </ResponsiveContainer>
      );
    }
    return (
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.2} />
              <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-light)" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} tickFormatter={(v) => `$${v}`} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${Number(v).toFixed(2)}`, cumulative ? 'Cumulative' : 'Daily Spend']} />
          <Area type="monotone" dataKey="amount" stroke="var(--chart-1)" fillOpacity={1} fill="url(#costGradient)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Cost Explorer" description={`${costs.period_start} to ${costs.period_end}`} icon={DollarSign}>
        <Button variant="ghost" size="sm" icon={Bookmark} onClick={() => setShowFilters(true)}>
          Saved{savedFilters.length > 0 && ` (${savedFilters.length})`}
        </Button>
        <Button variant="secondary" size="sm" icon={Save} onClick={() => setShowSaveFilter(true)}>Save View</Button>
        <Button variant="secondary" size="sm" icon={Download} onClick={exportCSV}>Export</Button>
      </PageHeader>

      {/* Controls toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {[7, 14, 30, 60, 90].map((d) => (
            <button key={d} onClick={() => setDays(d)} className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all duration-150" style={{ backgroundColor: days === d ? 'var(--brand-600)' : 'transparent', color: days === d ? 'white' : 'var(--color-text-secondary)' }}>
              {d}d
            </button>
          ))}
        </div>
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {CHART_TYPES.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setChartType(id)} className="p-1.5 rounded-[var(--radius-sm)] transition-all duration-150" style={{ backgroundColor: chartType === id ? 'var(--brand-600)' : 'transparent', color: chartType === id ? 'white' : 'var(--color-text-secondary)' }} title={label}>
              <Icon size={16} />
            </button>
          ))}
        </div>
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {DATE_BINS.map(({ id, label }) => (
            <button key={id} onClick={() => setDateBin(id)} className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all duration-150" style={{ backgroundColor: dateBin === id ? 'var(--brand-600)' : 'transparent', color: dateBin === id ? 'white' : 'var(--color-text-secondary)' }}>
              {label}
            </button>
          ))}
        </div>
        <div className="relative">
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)} className="appearance-none pl-3 pr-8 py-1.5 text-xs font-semibold rounded-[var(--radius-md)] cursor-pointer" style={{ backgroundColor: 'var(--color-surface-secondary)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }}>
            {GROUP_BY_OPTIONS.map(({ id, label }) => (<option key={id} value={id}>{label}</option>))}
          </select>
          <Layers size={12} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-tertiary)' }} />
        </div>
        <button onClick={() => setCumulative(!cumulative)} className="px-3 py-1.5 rounded-[var(--radius-md)] text-xs font-semibold transition-all duration-150" style={{ backgroundColor: cumulative ? 'var(--brand-600)' : 'var(--color-surface-secondary)', color: cumulative ? 'white' : 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }}>
          Cumulative
        </button>
      </div>

      {/* Total banner */}
      <div className="rounded-[var(--radius-lg)] p-6 text-white mb-6" style={{ background: 'linear-gradient(135deg, var(--brand-700), var(--brand-600))' }}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <p className="text-sm opacity-70">Total Spend</p>
            <p className="text-4xl font-bold">${costs.total_spend.toFixed(2)}</p>
            <p className="text-sm mt-1 opacity-60">Avg ${avgDay.toFixed(2)}/day &middot; {costs.daily_totals.length} days</p>
          </div>
          <div className="flex gap-6 text-right">
            <div>
              <p className="text-sm opacity-70">Services</p>
              <p className="text-2xl font-bold">{costs.by_service.length}</p>
            </div>
            <div>
              <p className="text-sm opacity-70">Top Service</p>
              <p className="text-lg font-bold">{costs.by_service[0]?.service || 'N/A'}</p>
              <p className="text-xs opacity-60">${costs.by_service[0]?.amount.toFixed(2) || '0'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>
            {cumulative ? 'Cumulative' : dateBin.charAt(0).toUpperCase() + dateBin.slice(1)} Spend{chartType === 'pie' ? ' Distribution' : ' Trend'}
          </CardTitle>
          <div className="flex items-center gap-2">
            {groupBy !== 'none' && chartType !== 'pie' && <Badge variant="brand">{GROUP_BY_OPTIONS.find((g) => g.id === groupBy)?.label}</Badge>}
          </div>
        </CardHeader>
        {renderChart()}
      </Card>

      {/* Service breakdown table */}
      <Card>
        <CardHeader>
          <CardTitle>Service Breakdown</CardTitle>
          <Badge variant="neutral">{costs.by_service.length} services</Badge>
        </CardHeader>
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
              <th className="pb-3 font-semibold">Service</th>
              <th className="pb-3 font-semibold text-right">Amount</th>
              <th className="pb-3 font-semibold text-right">% of Total</th>
              <th className="pb-3 font-semibold text-right">Avg/Day</th>
            </tr>
          </thead>
          <tbody>
            {costs.by_service.map((svc, i) => {
              const pct = costs.total_spend > 0 ? (svc.amount / costs.total_spend) * 100 : 0;
              const avg = svc.amount / (costs.daily_totals.length || 1);
              return (
                <tr key={i} className="transition-colors hover:bg-[var(--color-surface-hover)]" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td className="py-3 text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                      {svc.service}
                    </div>
                  </td>
                  <td className="py-3 text-sm text-right font-semibold" style={{ color: 'var(--color-text-primary)' }}>${svc.amount.toFixed(2)}</td>
                  <td className="py-3 text-sm text-right" style={{ color: 'var(--color-text-secondary)' }}>
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                        <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                      </div>
                      {pct.toFixed(1)}%
                    </div>
                  </td>
                  <td className="py-3 text-sm text-right" style={{ color: 'var(--color-text-tertiary)' }}>${avg.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Save Filter Modal */}
      <Modal open={showSaveFilter} onClose={() => setShowSaveFilter(false)} title="Save Current View">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Filter Name</label>
            <input value={filterName} onChange={(e) => setFilterName(e.target.value)} placeholder="e.g., Last 30 days by service" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} autoFocus />
          </div>
          <div className="flex flex-wrap gap-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            <Badge variant="neutral">{days}d</Badge>
            <Badge variant="neutral">{chartType}</Badge>
            <Badge variant="neutral">{dateBin}</Badge>
            <Badge variant="neutral">{groupBy}</Badge>
            {cumulative && <Badge variant="brand">cumulative</Badge>}
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={() => setShowSaveFilter(false)}>Cancel</Button>
            <Button size="sm" onClick={saveCurrentFilter}>Save Filter</Button>
          </div>
        </div>
      </Modal>

      {/* Saved Filters Modal */}
      <Modal open={showFilters} onClose={() => setShowFilters(false)} title="Saved Filters">
        {savedFilters.length === 0 ? (
          <div className="text-center py-8">
            <Bookmark size={32} style={{ color: 'var(--color-text-tertiary)' }} className="mx-auto mb-3" />
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>No saved filters yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {savedFilters.map((f) => (
              <div key={f.id} className="flex items-center justify-between p-3 rounded-[var(--radius-md)] hover:bg-[var(--color-surface-hover)] cursor-pointer transition-colors" style={{ border: '1px solid var(--color-border-light)' }}>
                <div onClick={() => loadFilter(f)} className="flex-1">
                  <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{f.name}</p>
                  <div className="flex gap-1.5 mt-1">
                    <Badge variant="neutral" size="sm">{f.days}d</Badge>
                    <Badge variant="neutral" size="sm">{f.chartType}</Badge>
                    <Badge variant="neutral" size="sm">{f.dateBin}</Badge>
                  </div>
                </div>
                <button onClick={() => deleteFilter(f.id)} className="p-1.5 rounded hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-tertiary)' }}>
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
}

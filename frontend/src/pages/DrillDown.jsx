import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, TrendingDown, Minus, ArrowUpRight, ArrowDownRight, HelpCircle } from 'lucide-react';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Badge } from '../components/ui/Badge';
import { SkeletonCard, SkeletonChart, SkeletonTable, Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

const COLORS_UP = 'var(--color-error)';
const COLORS_DOWN = 'var(--color-success)';

function formatPct(value) {
  if (!value && value !== 0) return '—';
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`;
}

function formatDollar(value) {
  if (!value && value !== 0) return '$0.00';
  return `${value >= 0 ? '+' : '-'}$${Math.abs(value).toFixed(2)}`;
}

function DirectionIcon({ direction, size = 20 }) {
  if (direction === 'increase') return <TrendingUp size={size} className="text-red-500" />;
  if (direction === 'decrease') return <TrendingDown size={size} className="text-green-500" />;
  return <Minus size={size} className="text-gray-400" />;
}

function ChangeBadge({ change, changePct }) {
  const isUp = change > 0;
  const isDown = change < 0;

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
      isUp ? 'bg-red-50 text-red-700' : isDown ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-600'
    }`}>
      {isUp ? <ArrowUpRight size={12} /> : isDown ? <ArrowDownRight size={12} /> : null}
      {formatDollar(change)} ({formatPct(changePct)})
    </div>
  );
}

export default function DrillDown() {
  const [data, setData] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState('week');
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const accountsData = await api.getAccounts();
        setAccounts(accountsData);

        if (accountsData.length > 0) {
          const drillDown = await api.getDrillDown(accountsData[0].id, mode);
          setData(drillDown);
        }
      } catch (err) {
        console.error(err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [mode]);

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="flex items-center justify-between mb-8">
          <div><Skeleton variant="text" className="w-56 h-7 mb-2" /><Skeleton variant="text" className="w-72 h-4" /></div>
        </div>
        <div className="grid grid-cols-3 gap-4 mb-6 stagger-children"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
        <SkeletonChart className="mb-6" />
        <SkeletonTable rows={6} cols={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[var(--radius-lg)] p-4 text-sm animate-fadeIn" style={{ backgroundColor: 'var(--color-error-bg)', color: 'var(--color-error-text)', border: '1px solid var(--color-error)' }}>
        {error}
      </div>
    );
  }

  if (!data) {
    return <EmptyState icon={HelpCircle} title="No account connected" description="Connect an AWS account to analyze cost changes." />;
  }

  // Prepare chart data — top 10 service changes sorted by absolute change
  const chartData = data.service_changes.slice(0, 10).map((s) => ({
    name: s.service.replace('Amazon ', '').replace('AWS ', ''),
    change: s.change,
    direction: s.direction,
  }));

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <PageHeader
        title="Why did costs change?"
        description={`${data.current_period.start} to ${data.current_period.end} vs ${data.previous_period.start} to ${data.previous_period.end}`}
        icon={HelpCircle}
      >
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {[
            { key: 'day', label: 'Day' },
            { key: 'week', label: 'Week' },
            { key: 'month', label: 'Month' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setMode(key)}
              className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all duration-150"
              style={{
                backgroundColor: mode === key ? 'var(--brand-600)' : 'transparent',
                color: mode === key ? 'white' : 'var(--color-text-secondary)',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </PageHeader>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 stagger-children">
        <Card>
          <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Current Period</p>
          <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>${data.current_period.total.toFixed(2)}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>{data.current_period.start} → {data.current_period.end}</p>
        </Card>
        <Card>
          <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>Previous Period</p>
          <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>${data.previous_period.total.toFixed(2)}</p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>{data.previous_period.start} → {data.previous_period.end}</p>
        </Card>
        <div
          className="rounded-[var(--radius-lg)] p-6"
          style={{
            backgroundColor: data.direction === 'increase' ? 'var(--color-error-bg)' : data.direction === 'decrease' ? 'var(--color-success-bg)' : 'var(--color-surface)',
            border: `1px solid ${data.direction === 'increase' ? 'var(--color-error)' : data.direction === 'decrease' ? 'var(--color-success)' : 'var(--color-border)'}`,
          }}
        >
          <p className="text-sm flex items-center gap-1" style={{ color: 'var(--color-text-secondary)' }}>
            Net Change <DirectionIcon direction={data.direction} size={16} />
          </p>
          <p className="text-2xl font-bold" style={{ color: data.direction === 'increase' ? 'var(--color-error-text)' : data.direction === 'decrease' ? 'var(--color-success-text)' : 'var(--color-text-primary)' }}>
            {formatDollar(data.total_change)}
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>{formatPct(data.total_change_pct)} change</p>
        </div>
      </div>

      {/* Impact chart */}
      {chartData.length > 0 && (
        <Card className="mb-6">
          <CardTitle>Cost Impact by Service</CardTitle>
          <ResponsiveContainer width="100%" height={Math.max(250, chartData.length * 40)}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 120, right: 40 }}>
              <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(0)}`} tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value) => [`${formatDollar(value)}`, 'Change']}
              contentStyle={{ backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
              />
              <Bar dataKey="change" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={entry.direction === 'increase' ? COLORS_UP : COLORS_DOWN}
                    fillOpacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Service change table */}
      <Card className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <CardTitle>All Service Changes</CardTitle>
          <Badge variant="neutral">{data.service_changes.length} services</Badge>
        </div>
        {data.service_changes.length === 0 ? (
          <p className="text-center py-8" style={{ color: 'var(--color-text-tertiary)' }}>No cost changes detected for this period</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                <th className="pb-3 font-semibold">Service</th>
                <th className="pb-3 font-semibold text-right">Previous</th>
                <th className="pb-3 font-semibold text-right">Current</th>
                <th className="pb-3 font-semibold text-right">Change</th>
                <th className="pb-3 font-semibold text-right">Impact</th>
              </tr>
            </thead>
            <tbody>
              {data.service_changes.map((svc, i) => (
                <tr key={i} className="transition-colors" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td className="py-3 text-sm flex items-center gap-2" style={{ color: 'var(--color-text-primary)' }}>
                    <DirectionIcon direction={svc.direction} size={16} />
                    {svc.service}
                  </td>
                  <td className="py-3 text-sm text-right" style={{ color: 'var(--color-text-tertiary)' }}>
                    ${svc.previous_amount.toFixed(2)}
                  </td>
                  <td className="py-3 text-sm text-right font-medium" style={{ color: 'var(--color-text-primary)' }}>
                    ${svc.current_amount.toFixed(2)}
                  </td>
                  <td className="py-3 text-sm text-right">
                    <ChangeBadge change={svc.change} changePct={svc.change_pct} />
                  </td>
                  <td className="py-3 text-sm text-right" style={{ color: 'var(--color-text-secondary)' }}>
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(svc.impact_pct * 100, 100)}%`,
                            backgroundColor: svc.direction === 'increase' ? 'var(--color-error)' : 'var(--color-success)',
                          }}
                        />
                      </div>
                      {(svc.impact_pct * 100).toFixed(0)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* New / Removed services callouts */}
      {(data.new_services.length > 0 || data.removed_services.length > 0) && (
        <div className="grid grid-cols-2 gap-4">
          {data.new_services.length > 0 && (
            <div className="bg-amber-50 rounded-xl border border-amber-200 p-5">
              <h3 className="text-sm font-semibold text-amber-800 mb-2">🆕 New Services</h3>
              {data.new_services.map((svc, i) => (
                <div key={i} className="text-sm text-amber-700 py-1">
                  {svc.service}: <span className="font-medium">${svc.current_amount.toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}
          {data.removed_services.length > 0 && (
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-5">
              <h3 className="text-sm font-semibold text-blue-800 mb-2">🗑️ Removed Services</h3>
              {data.removed_services.map((svc, i) => (
                <div key={i} className="text-sm text-blue-700 py-1">
                  {svc.service}: saved <span className="font-medium">${Math.abs(svc.previous_amount).toFixed(2)}/period</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

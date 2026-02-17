import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import {
  DollarSign, Server, AlertTriangle, Lightbulb, TrendingUp, Sparkles,
  ArrowRight, Wallet, Eye, BarChart3,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { StatCard } from '../components/ui/StatCard';
import { Card, CardTitle } from '../components/ui/Card';
import { SkeletonCard, SkeletonChart, Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

const COLORS = [
  'var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)',
  'var(--chart-5)', 'var(--chart-6)', 'var(--chart-7)', 'var(--chart-8)',
];

function DashboardSkeleton() {
  return (
    <div className="animate-fadeIn">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Skeleton variant="text" className="w-40 h-7 mb-2" />
          <Skeleton variant="text" className="w-56 h-4" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
        <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <SkeletonChart className="lg:col-span-2" />
        <SkeletonChart />
      </div>
    </div>
  );
}

const chartTooltipStyle = {
  backgroundColor: 'var(--color-surface-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-md)',
  color: 'var(--color-text-primary)',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [costs, setCosts] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [insight, setInsight] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadAccounts() {
      try {
        const [summaryData, accountsData] = await Promise.all([
          api.getDashboardSummary(),
          api.getAccounts(),
        ]);
        setSummary(summaryData);
        setAccounts(accountsData);
        if (accountsData.length > 0 && !selectedAccountId) {
          setSelectedAccountId(accountsData[0].id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadAccounts();
  }, []);

  useEffect(() => {
    if (!selectedAccountId) return;
    async function loadAccountData() {
      try {
        const [costsData, forecastData, insightData] = await Promise.all([
          api.getCosts(selectedAccountId),
          api.getForecast(selectedAccountId).catch(() => null),
          api.getInsights(selectedAccountId).catch(() => null),
        ]);
        setCosts(costsData);
        setForecast(forecastData);
        setInsight(insightData);
      } catch (err) {
        console.error(err);
      }
    }
    loadAccountData();
  }, [selectedAccountId]);

  if (loading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div
        className="rounded-[var(--radius-lg)] p-4 text-sm animate-fadeIn"
        style={{ backgroundColor: 'var(--color-error-bg)', color: 'var(--color-error-text)', border: '1px solid var(--color-error)' }}
      >
        Error: {error}
      </div>
    );
  }

  if (accounts.length === 0) {
    return (
      <EmptyState
        icon={Server}
        title="No AWS accounts connected"
        description="Connect your first AWS account to start monitoring costs. Takes less than 5 minutes with our CloudFormation template."
        actionLabel="Go to Settings"
        onAction={() => navigate('/settings')}
      />
    );
  }

  const dailyData = costs?.daily_totals?.map((d) => ({
    date: d.date.slice(5),
    amount: d.amount,
  })) || [];

  const serviceData = costs?.by_service?.map((s, i) => ({
    name: s.service.replace('Amazon ', '').replace('AWS ', ''),
    value: s.amount,
    color: COLORS[i % COLORS.length],
  })) || [];

  const totalSpend = costs?.total_spend || 0;

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Dashboard</h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            Overview of your AWS spending
          </p>
        </div>
        {accounts.length > 1 && (
          <select
            value={selectedAccountId || ''}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            className="px-3 py-2 text-sm rounded-[var(--radius-md)] outline-none"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
            }}
          >
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.account_name || acc.aws_account_id}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
        <StatCard
          icon={DollarSign}
          label="Month-to-Date Spend"
          value={`$${summary?.mtd_spend?.toFixed(2) || '0.00'}`}
        />
        <StatCard
          icon={Server}
          label="Active Accounts"
          value={summary?.active_accounts || 0}
        />
        <StatCard
          icon={AlertTriangle}
          label="Active Anomalies"
          value={summary?.active_anomalies || 0}
        />
        <StatCard
          icon={Lightbulb}
          label="Potential Savings"
          value={`$${summary?.potential_monthly_savings?.toFixed(2) || '0.00'}/mo`}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8 stagger-children">
        {[
          { icon: Eye, label: 'View Costs', to: '/costs' },
          { icon: Wallet, label: 'Check Budgets', to: '/budgets' },
          { icon: BarChart3, label: 'Why? Drill-Down', to: '/why' },
          { icon: Lightbulb, label: 'Savings Tips', to: '/recommendations' },
        ].map(({ icon: Icon, label, to }) => (
          <button
            key={to}
            onClick={() => navigate(to)}
            className="flex items-center gap-3 px-4 py-3 rounded-[var(--radius-md)] text-sm font-medium transition-all duration-150 group"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <Icon size={16} style={{ color: 'var(--brand-500)' }} />
            <span className="flex-1 text-left">{label}</span>
            <ArrowRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--color-text-tertiary)' }} />
          </button>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Cost Trend */}
        <Card className="lg:col-span-2">
          <CardTitle>Daily Spend (Last 30 Days)</CardTitle>
          {dailyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={dailyData}>
                <defs>
                  <linearGradient id="dashGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} interval={2} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} tickFormatter={(v) => `$${v}`} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => [`$${value.toFixed(2)}`, 'Spend']} labelFormatter={(l) => `Date: ${l}`} />
                <Area type="monotone" dataKey="amount" stroke="var(--chart-1)" fill="url(#dashGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64" style={{ color: 'var(--color-text-tertiary)' }}>
              No cost data available
            </div>
          )}
        </Card>

        {/* Service Breakdown */}
        <Card>
          <CardTitle>Spend by Service</CardTitle>
          {serviceData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={serviceData}
                    cx="50%" cy="50%"
                    innerRadius={50} outerRadius={80}
                    dataKey="value" paddingAngle={2}
                  >
                    {serviceData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => `$${value.toFixed(2)}`} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {serviceData.map((s, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                      <span className="truncate max-w-[140px]" style={{ color: 'var(--color-text-secondary)' }}>{s.name}</span>
                    </div>
                    <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>${s.value.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64" style={{ color: 'var(--color-text-tertiary)' }}>
              No data available
            </div>
          )}
        </Card>
      </div>

      {/* Forecast + Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6 stagger-children">
        {forecast && (
          <div
            className="rounded-[var(--radius-lg)] p-6 text-white"
            style={{ background: 'linear-gradient(135deg, var(--brand-700), var(--brand-600), #7c3aed)' }}
          >
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp size={20} className="opacity-70" />
              <h2 className="text-lg font-semibold">Monthly Forecast</h2>
            </div>
            <p className="text-4xl font-bold">${forecast.total_forecast.toFixed(2)}</p>
            <p className="text-sm mt-1 opacity-70">Projected end-of-month spend</p>
            <div className="grid grid-cols-3 gap-3 mt-4 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.2)' }}>
              <div>
                <p className="text-xs opacity-60">MTD Spend</p>
                <p className="font-semibold">${forecast.mtd_spend.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs opacity-60">Daily Avg</p>
                <p className="font-semibold">${forecast.daily_avg.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs opacity-60">Days Left</p>
                <p className="font-semibold">{forecast.days_remaining}</p>
              </div>
            </div>
            <p className="text-xs opacity-50 mt-3">Source: {forecast.source === 'aws' ? 'AWS Cost Explorer' : 'Linear projection'}</p>
          </div>
        )}

        {costs && (
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  Total Spend ({costs.period_start} to {costs.period_end})
                </p>
                <p className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>${totalSpend.toFixed(2)}</p>
              </div>
              <div className="text-right text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
                <p>{costs.by_service.length} services</p>
                <p>{costs.daily_totals.length} days</p>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* AI Insight */}
      {insight && (
        <div
          className="mt-6 rounded-[var(--radius-lg)] p-6 animate-fadeInUp"
          style={{
            background: 'var(--color-warning-bg)',
            border: '1px solid var(--color-warning)',
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={20} style={{ color: 'var(--color-warning)' }} />
            <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>AI Cost Insight</h2>
          </div>
          <p className="leading-relaxed text-sm" style={{ color: 'var(--color-text-secondary)' }}>{insight.insight}</p>
        </div>
      )}
    </div>
  );
}

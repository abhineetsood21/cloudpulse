import { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend, AreaChart, Area } from 'recharts';
import { Shield, TrendingDown, DollarSign, Clock, BarChart3 } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Badge } from '../components/ui/Badge';
import { StatCard } from '../components/ui/StatCard';

const CHART_COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)'];
const chartTooltipStyle = { backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' };

const COVERAGE_DATA = [
  { month: 'Sep', onDemand: 2800, savingsPlans: 900, reserved: 400, spot: 120 },
  { month: 'Oct', onDemand: 2650, savingsPlans: 1050, reserved: 400, spot: 150 },
  { month: 'Nov', onDemand: 2400, savingsPlans: 1200, reserved: 450, spot: 180 },
  { month: 'Dec', onDemand: 2200, savingsPlans: 1350, reserved: 500, spot: 200 },
  { month: 'Jan', onDemand: 2050, savingsPlans: 1500, reserved: 500, spot: 230 },
  { month: 'Feb', onDemand: 1900, savingsPlans: 1650, reserved: 550, spot: 185 },
];

const COMMITMENT_BREAKDOWN = [
  { name: 'On-Demand', value: 1900 },
  { name: 'Savings Plans', value: 1650 },
  { name: 'Reserved Instances', value: 550 },
  { name: 'Spot', value: 185 },
];

const COMMITMENTS = [
  { id: 1, type: 'Compute Savings Plan', service: 'EC2, Fargate, Lambda', commitment: '$0.042/hr', term: '1 Year', upfront: 'No Upfront', monthlySavings: 180.50, utilization: 94, expiry: '2026-08-15' },
  { id: 2, type: 'EC2 Instance Savings Plan', service: 'EC2 (m5.xlarge)', commitment: '$0.031/hr', term: '1 Year', upfront: 'Partial', monthlySavings: 95.20, utilization: 87, expiry: '2026-06-01' },
  { id: 3, type: 'Reserved Instance', service: 'RDS (db.r5.large)', commitment: '$145.00/mo', term: '1 Year', upfront: 'No Upfront', monthlySavings: 62.00, utilization: 100, expiry: '2026-03-20' },
  { id: 4, type: 'Reserved Instance', service: 'ElastiCache (r6g.large)', commitment: '$98.00/mo', term: '1 Year', upfront: 'All Upfront', monthlySavings: 45.30, utilization: 100, expiry: '2026-11-10' },
];

export default function FinancialCommitments() {
  const [tab, setTab] = useState('overview');

  const totalSpend = COMMITMENT_BREAKDOWN.reduce((s, c) => s + c.value, 0);
  const committedSpend = totalSpend - COMMITMENT_BREAKDOWN[0].value;
  const savingsRate = ((committedSpend / totalSpend) * 0.35 * 100).toFixed(1);
  const totalMonthlySavings = COMMITMENTS.reduce((s, c) => s + c.monthlySavings, 0);
  const coveragePct = ((committedSpend / totalSpend) * 100).toFixed(1);

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Financial Commitments" description="Track Savings Plans, Reserved Instances, and commitment coverage" icon={Shield} />

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Shield} label="Coverage Rate" value={`${coveragePct}%`} trend={-8.2} trendLabel="vs last month" />
        <StatCard icon={TrendingDown} label="Effective Savings" value={`${savingsRate}%`} trendLabel="of eligible spend" />
        <StatCard icon={DollarSign} label="Monthly Savings" value={`$${totalMonthlySavings.toFixed(0)}`} trendLabel={`${COMMITMENTS.length} active commitments`} />
        <StatCard icon={Clock} label="Expiring Soon" value="1" trendLabel="Within 60 days" trend={3} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-[var(--radius-md)] mb-6 inline-flex" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
        {['overview', 'commitments'].map((t) => (
          <button key={t} onClick={() => setTab(t)} className="px-4 py-2 rounded-[var(--radius-sm)] text-sm font-medium transition-all capitalize" style={{ backgroundColor: tab === t ? 'var(--brand-600)' : 'transparent', color: tab === t ? 'white' : 'var(--color-text-secondary)' }}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'overview' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardTitle className="mb-4">Coverage Trend</CardTitle>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={COVERAGE_DATA}>
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${v}`, '']} />
                  <Area type="monotone" dataKey="spot" stackId="1" stroke="var(--chart-4)" fill="var(--chart-4)" fillOpacity={0.6} name="Spot" />
                  <Area type="monotone" dataKey="reserved" stackId="1" stroke="var(--chart-3)" fill="var(--chart-3)" fillOpacity={0.6} name="Reserved" />
                  <Area type="monotone" dataKey="savingsPlans" stackId="1" stroke="var(--chart-2)" fill="var(--chart-2)" fillOpacity={0.6} name="Savings Plans" />
                  <Area type="monotone" dataKey="onDemand" stackId="1" stroke="var(--chart-1)" fill="var(--chart-1)" fillOpacity={0.3} name="On-Demand" />
                  <Legend />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>
          <Card>
            <CardTitle className="mb-4">Spend Breakdown</CardTitle>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={COMMITMENT_BREAKDOWN} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}>
                  {COMMITMENT_BREAKDOWN.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${v}`, '']} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </div>
      ) : (
        <Card padding={false}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                  <th className="px-6 py-3 font-semibold">Commitment</th>
                  <th className="px-6 py-3 font-semibold">Service</th>
                  <th className="px-6 py-3 font-semibold">Term</th>
                  <th className="px-6 py-3 font-semibold text-right">Savings/mo</th>
                  <th className="px-6 py-3 font-semibold text-right">Utilization</th>
                  <th className="px-6 py-3 font-semibold">Expiry</th>
                </tr>
              </thead>
              <tbody>
                {COMMITMENTS.map((c) => (
                  <tr key={c.id} className="hover:bg-[var(--color-surface-hover)] transition-colors" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                    <td className="px-6 py-3">
                      <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{c.type}</p>
                      <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{c.commitment} · {c.upfront}</p>
                    </td>
                    <td className="px-6 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{c.service}</td>
                    <td className="px-6 py-3"><Badge variant="neutral" size="sm">{c.term}</Badge></td>
                    <td className="px-6 py-3 text-sm text-right font-semibold" style={{ color: 'var(--color-success-text)' }}>${c.monthlySavings.toFixed(2)}</td>
                    <td className="px-6 py-3 text-right">
                      <div className="inline-flex items-center gap-2">
                        <div className="w-12 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                          <div className="h-full rounded-full" style={{ width: `${c.utilization}%`, backgroundColor: c.utilization > 90 ? 'var(--color-success)' : 'var(--color-warning)' }} />
                        </div>
                        <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>{c.utilization}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant={new Date(c.expiry) < new Date(Date.now() + 60 * 86400000) ? 'warning' : 'neutral'} size="sm">{c.expiry}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

import { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { Network, ArrowRightLeft, Globe, AlertTriangle, DollarSign } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Badge } from '../components/ui/Badge';
import { StatCard } from '../components/ui/StatCard';

const CHART_COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)', 'var(--chart-6)'];
const chartTooltipStyle = { backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' };

const EGRESS_DATA = [
  { destination: 'Internet (Public)', cost: 285.40, gb: 3200, category: 'Egress' },
  { destination: 'Cross-AZ (us-east-1a→1b)', cost: 124.80, gb: 12400, category: 'Cross-AZ' },
  { destination: 'Cross-AZ (us-east-1a→1c)', cost: 98.50, gb: 9800, category: 'Cross-AZ' },
  { destination: 'S3 Gateway', cost: 0, gb: 8500, category: 'Free' },
  { destination: 'NAT Gateway Processing', cost: 156.30, gb: 3450, category: 'NAT' },
  { destination: 'VPC Peering (us-west-2)', cost: 45.20, gb: 4500, category: 'Peering' },
  { destination: 'Datadog (egress)', cost: 32.10, gb: 350, category: 'SaaS Egress' },
  { destination: 'CloudFront Origin', cost: 18.90, gb: 1890, category: 'CDN' },
];

const FLOW_TABLE = [
  { source: 'vpc-prod/us-east-1a', destination: 'vpc-prod/us-east-1b', protocol: 'TCP/443', bytes: '1.2 TB', cost: 62.40, type: 'Cross-AZ' },
  { source: 'vpc-prod/us-east-1a', destination: 'Internet', protocol: 'TCP/443', bytes: '890 GB', cost: 82.30, type: 'Egress' },
  { source: 'vpc-prod/us-east-1b', destination: 'vpc-prod/us-east-1c', protocol: 'TCP/5432', bytes: '780 GB', cost: 39.00, type: 'Cross-AZ' },
  { source: 'nat-0a1b2c3d', destination: 'Internet', protocol: 'ALL', bytes: '3.4 TB', cost: 156.30, type: 'NAT' },
  { source: 'vpc-prod/us-east-1a', destination: 'vpce-s3', protocol: 'TCP/443', bytes: '8.5 TB', cost: 0, type: 'Gateway Endpoint' },
  { source: 'vpc-prod/us-east-1a', destination: 'pcx-west2', protocol: 'TCP/443', bytes: '4.5 TB', cost: 45.20, type: 'Peering' },
  { source: 'vpc-prod/us-east-1b', destination: 'Internet', protocol: 'TCP/443', bytes: '420 GB', cost: 38.70, type: 'Egress' },
  { source: 'vpc-prod/us-east-1a', destination: 'cf-dist-E1A2B3', protocol: 'TCP/443', bytes: '1.9 TB', cost: 18.90, type: 'CDN' },
];

export default function NetworkFlow() {
  const [tab, setTab] = useState('overview');

  const totalNetworkCost = EGRESS_DATA.reduce((s, d) => s + d.cost, 0);
  const crossAzCost = EGRESS_DATA.filter((d) => d.category === 'Cross-AZ').reduce((s, d) => s + d.cost, 0);
  const egressCost = EGRESS_DATA.filter((d) => d.category === 'Egress').reduce((s, d) => s + d.cost, 0);
  const chartData = EGRESS_DATA.filter((d) => d.cost > 0).sort((a, b) => b.cost - a.cost);

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Network Flow" description="Analyze network traffic costs including cross-AZ, egress, and NAT charges" icon={Network} />

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <StatCard icon={DollarSign} label="Total Network Cost" value={`$${totalNetworkCost.toFixed(0)}/mo`} trendLabel="data transfer charges" />
        <StatCard icon={ArrowRightLeft} label="Cross-AZ Cost" value={`$${crossAzCost.toFixed(0)}/mo`} trend={8} trendLabel="optimization possible" />
        <StatCard icon={Globe} label="Egress Cost" value={`$${egressCost.toFixed(0)}/mo`} trendLabel="to internet" />
        <StatCard icon={AlertTriangle} label="NAT Gateway" value={`$${EGRESS_DATA.find((d) => d.category === 'NAT')?.cost.toFixed(0) || 0}/mo`} trend={15} trendLabel="high processing cost" />
      </div>

      <div className="flex gap-1 p-1 rounded-[var(--radius-md)] mb-6 inline-flex" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
        {['overview', 'flows'].map((t) => (
          <button key={t} onClick={() => setTab(t)} className="px-4 py-2 rounded-[var(--radius-sm)] text-sm font-medium transition-all capitalize" style={{ backgroundColor: tab === t ? 'var(--brand-600)' : 'transparent', color: tab === t ? 'white' : 'var(--color-text-secondary)' }}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'overview' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardTitle className="mb-4">Cost by Destination</CardTitle>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={chartData} layout="vertical">
                <XAxis type="number" tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="destination" tick={{ fontSize: 10, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} width={150} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name, props) => [`$${v.toFixed(2)} · ${props.payload.gb.toLocaleString()} GB`, 'Cost']} />
                <Bar dataKey="cost" radius={[0, 4, 4, 0]}>
                  {chartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <CardTitle className="mb-4">Cost Breakdown by Category</CardTitle>
            <div className="space-y-3 mt-6">
              {['Egress', 'Cross-AZ', 'NAT', 'Peering', 'SaaS Egress', 'CDN'].map((cat) => {
                const catCost = EGRESS_DATA.filter((d) => d.category === cat).reduce((s, d) => s + d.cost, 0);
                const pct = totalNetworkCost > 0 ? (catCost / totalNetworkCost) * 100 : 0;
                if (catCost === 0) return null;
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{cat}</span>
                      <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>${catCost.toFixed(2)}</span>
                    </div>
                    <div className="w-full h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: 'var(--brand-500)' }} />
                    </div>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-tertiary)' }}>{pct.toFixed(1)}% of total</p>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      ) : (
        <Card padding={false}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                  <th className="px-6 py-3 font-semibold">Source</th>
                  <th className="px-6 py-3 font-semibold">Destination</th>
                  <th className="px-6 py-3 font-semibold">Type</th>
                  <th className="px-6 py-3 font-semibold">Protocol</th>
                  <th className="px-6 py-3 font-semibold text-right">Data</th>
                  <th className="px-6 py-3 font-semibold text-right">Cost</th>
                </tr>
              </thead>
              <tbody>
                {FLOW_TABLE.map((f, i) => (
                  <tr key={i} className="hover:bg-[var(--color-surface-hover)] transition-colors" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                    <td className="px-6 py-3 text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{f.source}</td>
                    <td className="px-6 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{f.destination}</td>
                    <td className="px-6 py-3"><Badge variant={f.type === 'Cross-AZ' ? 'warning' : f.type === 'Gateway Endpoint' ? 'success' : 'neutral'} size="sm">{f.type}</Badge></td>
                    <td className="px-6 py-3 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{f.protocol}</td>
                    <td className="px-6 py-3 text-sm text-right" style={{ color: 'var(--color-text-secondary)' }}>{f.bytes}</td>
                    <td className="px-6 py-3 text-sm text-right font-semibold" style={{ color: f.cost === 0 ? 'var(--color-success-text)' : 'var(--color-text-primary)' }}>{f.cost === 0 ? 'Free' : `$${f.cost.toFixed(2)}`}</td>
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

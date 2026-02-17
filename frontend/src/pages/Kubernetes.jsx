import { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts';
import { Container, Cpu, HardDrive, AlertTriangle, TrendingDown } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Badge } from '../components/ui/Badge';
import { StatCard } from '../components/ui/StatCard';

const CHART_COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)', 'var(--chart-6)'];
const chartTooltipStyle = { backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' };

const CLUSTERS = [
  { name: 'prod-eks-us-east-1', region: 'us-east-1', nodes: 12, pods: 87, monthlyCost: 2450.00, cpuUtil: 62, memUtil: 71, idleCost: 380.50 },
  { name: 'staging-eks-us-east-1', region: 'us-east-1', nodes: 4, pods: 23, monthlyCost: 680.00, cpuUtil: 35, memUtil: 42, idleCost: 290.00 },
  { name: 'dev-eks-us-west-2', region: 'us-west-2', nodes: 3, pods: 15, monthlyCost: 420.00, cpuUtil: 28, memUtil: 33, idleCost: 210.00 },
];

const NAMESPACES = [
  { name: 'api-gateway', pods: 6, cpuReq: '2.0', cpuUsed: '1.4', memReq: '4Gi', memUsed: '2.8Gi', monthlyCost: 450.00, efficiency: 70 },
  { name: 'user-service', pods: 4, cpuReq: '1.5', cpuUsed: '0.9', memReq: '3Gi', memUsed: '1.8Gi', monthlyCost: 320.00, efficiency: 60 },
  { name: 'payment-service', pods: 3, cpuReq: '1.0', cpuUsed: '0.8', memReq: '2Gi', memUsed: '1.6Gi', monthlyCost: 280.00, efficiency: 80 },
  { name: 'notification-svc', pods: 2, cpuReq: '0.5', cpuUsed: '0.1', memReq: '1Gi', memUsed: '0.3Gi', monthlyCost: 150.00, efficiency: 25 },
  { name: 'analytics', pods: 8, cpuReq: '4.0', cpuUsed: '3.2', memReq: '8Gi', memUsed: '6.5Gi', monthlyCost: 680.00, efficiency: 81 },
  { name: 'monitoring', pods: 5, cpuReq: '1.5', cpuUsed: '1.0', memReq: '3Gi', memUsed: '2.2Gi', monthlyCost: 290.00, efficiency: 67 },
  { name: 'kube-system', pods: 12, cpuReq: '1.0', cpuUsed: '0.5', memReq: '2Gi', memUsed: '1.0Gi', monthlyCost: 180.00, efficiency: 50 },
];

const RIGHTSIZING = [
  { namespace: 'notification-svc', pod: 'notifier-7d8f9', currentCpu: '500m', suggestedCpu: '100m', currentMem: '1Gi', suggestedMem: '256Mi', savings: 85.00 },
  { namespace: 'kube-system', pod: 'coredns-abc12', currentCpu: '250m', suggestedCpu: '100m', currentMem: '512Mi', suggestedMem: '256Mi', savings: 25.00 },
  { namespace: 'user-service', pod: 'user-api-x9k2', currentCpu: '500m', suggestedCpu: '250m', currentMem: '1Gi', suggestedMem: '512Mi', savings: 45.00 },
];

export default function Kubernetes() {
  const [selectedCluster, setSelectedCluster] = useState(CLUSTERS[0].name);
  const [tab, setTab] = useState('namespaces');

  const cluster = CLUSTERS.find((c) => c.name === selectedCluster) || CLUSTERS[0];
  const namespaceCostData = NAMESPACES.map((n) => ({ name: n.name, cost: n.monthlyCost }));
  const efficiencyData = [{ name: 'Used', value: cluster.cpuUtil }, { name: 'Idle', value: 100 - cluster.cpuUtil }];
  const totalIdleCost = CLUSTERS.reduce((s, c) => s + c.idleCost, 0);
  const totalSavings = RIGHTSIZING.reduce((s, r) => s + r.savings, 0);

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Kubernetes Costs" description="Monitor cluster, namespace, and pod-level resource costs" icon={Container} />

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Container} label="Total Clusters" value={CLUSTERS.length} trendLabel={`${CLUSTERS.reduce((s, c) => s + c.nodes, 0)} nodes`} />
        <StatCard icon={Cpu} label="Avg CPU Utilization" value={`${Math.round(CLUSTERS.reduce((s, c) => s + c.cpuUtil, 0) / CLUSTERS.length)}%`} trendLabel="across all clusters" />
        <StatCard icon={AlertTriangle} label="Idle Cost" value={`$${totalIdleCost.toFixed(0)}/mo`} trend={12} trendLabel="optimization needed" />
        <StatCard icon={TrendingDown} label="Rightsizing Savings" value={`$${totalSavings.toFixed(0)}/mo`} trendLabel={`${RIGHTSIZING.length} suggestions`} />
      </div>

      {/* Cluster selector */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {CLUSTERS.map((c) => (
            <button key={c.name} onClick={() => setSelectedCluster(c.name)} className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all" style={{ backgroundColor: selectedCluster === c.name ? 'var(--brand-600)' : 'transparent', color: selectedCluster === c.name ? 'white' : 'var(--color-text-secondary)' }}>
              {c.name}
            </button>
          ))}
        </div>
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {['namespaces', 'rightsizing'].map((t) => (
            <button key={t} onClick={() => setTab(t)} className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all capitalize" style={{ backgroundColor: tab === t ? 'var(--brand-600)' : 'transparent', color: tab === t ? 'white' : 'var(--color-text-secondary)' }}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Cluster summary */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-6">
        <div className="rounded-[var(--radius-md)] p-3" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Nodes</p>
          <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>{cluster.nodes}</p>
        </div>
        <div className="rounded-[var(--radius-md)] p-3" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Pods</p>
          <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>{cluster.pods}</p>
        </div>
        <div className="rounded-[var(--radius-md)] p-3" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>CPU Util</p>
          <p className="text-lg font-bold" style={{ color: cluster.cpuUtil > 60 ? 'var(--color-success-text)' : 'var(--color-warning-text)' }}>{cluster.cpuUtil}%</p>
        </div>
        <div className="rounded-[var(--radius-md)] p-3" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Memory Util</p>
          <p className="text-lg font-bold" style={{ color: cluster.memUtil > 60 ? 'var(--color-success-text)' : 'var(--color-warning-text)' }}>{cluster.memUtil}%</p>
        </div>
        <div className="rounded-[var(--radius-md)] p-3" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Monthly Cost</p>
          <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>${cluster.monthlyCost.toFixed(0)}</p>
        </div>
      </div>

      {tab === 'namespaces' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card padding={false}>
              <div className="px-6 py-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
                <CardTitle>Namespace Breakdown</CardTitle>
              </div>
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                    <th className="px-6 py-3 font-semibold">Namespace</th>
                    <th className="px-6 py-3 font-semibold text-center">Pods</th>
                    <th className="px-6 py-3 font-semibold">CPU (req/used)</th>
                    <th className="px-6 py-3 font-semibold">Memory (req/used)</th>
                    <th className="px-6 py-3 font-semibold text-right">Cost/mo</th>
                    <th className="px-6 py-3 font-semibold text-right">Efficiency</th>
                  </tr>
                </thead>
                <tbody>
                  {NAMESPACES.map((n) => (
                    <tr key={n.name} className="hover:bg-[var(--color-surface-hover)] transition-colors" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                      <td className="px-6 py-3 text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{n.name}</td>
                      <td className="px-6 py-3 text-sm text-center" style={{ color: 'var(--color-text-secondary)' }}>{n.pods}</td>
                      <td className="px-6 py-3 text-xs" style={{ color: 'var(--color-text-secondary)' }}>{n.cpuUsed} / {n.cpuReq}</td>
                      <td className="px-6 py-3 text-xs" style={{ color: 'var(--color-text-secondary)' }}>{n.memUsed} / {n.memReq}</td>
                      <td className="px-6 py-3 text-sm text-right font-semibold" style={{ color: 'var(--color-text-primary)' }}>${n.monthlyCost.toFixed(0)}</td>
                      <td className="px-6 py-3 text-right">
                        <Badge variant={n.efficiency >= 70 ? 'success' : n.efficiency >= 50 ? 'warning' : 'error'} size="sm">{n.efficiency}%</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </div>
          <Card>
            <CardTitle className="mb-4">Cost by Namespace</CardTitle>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={namespaceCostData} layout="vertical">
                <XAxis type="number" tickFormatter={(v) => `$${v}`} tick={{ fontSize: 10, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} width={90} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${v}`, 'Cost']} />
                <Bar dataKey="cost" radius={[0, 4, 4, 0]}>
                  {namespaceCostData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      ) : (
        <Card padding={false}>
          <div className="px-6 py-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
            <CardTitle>Rightsizing Recommendations</CardTitle>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                <th className="px-6 py-3 font-semibold">Pod</th>
                <th className="px-6 py-3 font-semibold">Namespace</th>
                <th className="px-6 py-3 font-semibold">CPU (current → suggested)</th>
                <th className="px-6 py-3 font-semibold">Memory (current → suggested)</th>
                <th className="px-6 py-3 font-semibold text-right">Est. Savings</th>
              </tr>
            </thead>
            <tbody>
              {RIGHTSIZING.map((r, i) => (
                <tr key={i} className="hover:bg-[var(--color-surface-hover)] transition-colors" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td className="px-6 py-3 text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{r.pod}</td>
                  <td className="px-6 py-3"><Badge variant="neutral" size="sm">{r.namespace}</Badge></td>
                  <td className="px-6 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{r.currentCpu} → <span style={{ color: 'var(--color-success-text)' }}>{r.suggestedCpu}</span></td>
                  <td className="px-6 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{r.currentMem} → <span style={{ color: 'var(--color-success-text)' }}>{r.suggestedMem}</span></td>
                  <td className="px-6 py-3 text-sm text-right font-semibold" style={{ color: 'var(--color-success-text)' }}>${r.savings.toFixed(0)}/mo</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

import { useEffect, useState, useMemo } from 'react';
import { AlertTriangle, CheckCircle, TrendingUp, DollarSign, Activity, Settings2, Bell, Shield } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { SkeletonCard, Skeleton } from '../components/ui/Skeleton';
import { StatCard } from '../components/ui/StatCard';
import { Modal } from '../components/ui/Modal';

const severityVariant = { critical: 'error', warning: 'warning', info: 'info' };
const severityColor = { critical: 'var(--color-error)', warning: 'var(--color-warning)', info: 'var(--color-info)' };

const mockTimelineData = [
  { date: 'Mon', anomalies: 2, impact: 145.50 },
  { date: 'Tue', anomalies: 0, impact: 0 },
  { date: 'Wed', anomalies: 1, impact: 67.20 },
  { date: 'Thu', anomalies: 3, impact: 234.80 },
  { date: 'Fri', anomalies: 1, impact: 89.10 },
  { date: 'Sat', anomalies: 0, impact: 0 },
  { date: 'Sun', anomalies: 4, impact: 312.40 },
];

const alertDefaults = {
  criticalThreshold: 50,
  warningThreshold: 25,
  emailEnabled: true,
  slackEnabled: false,
  autoAcknowledge: false,
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-lg)' }}>
      <p className="font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }}>{entry.name}: {entry.name === 'impact' ? `$${entry.value.toFixed(2)}` : entry.value}</p>
      ))}
    </div>
  );
};

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showConfig, setShowConfig] = useState(false);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [alertConfig, setAlertConfig] = useState(() => {
    const saved = localStorage.getItem('cp_anomaly_config');
    return saved ? JSON.parse(saved) : alertDefaults;
  });

  useEffect(() => {
    async function load() {
      try {
        const accountsData = await api.getAccounts();
        setAccounts(accountsData);
        if (accountsData.length > 0) {
          const data = await api.getAnomalies(accountsData[0].id);
          setAnomalies(data);
        }
      } catch (err) { console.error(err); } finally { setLoading(false); }
    }
    load();
  }, []);

  const handleAcknowledge = async (id) => {
    try {
      await api.acknowledgeAnomaly(id);
      setAnomalies((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
    } catch (err) { console.error(err); }
  };

  const stats = useMemo(() => {
    const total = anomalies.length;
    const critical = anomalies.filter(a => a.severity === 'critical').length;
    const unacked = anomalies.filter(a => !a.acknowledged).length;
    const totalImpact = anomalies.reduce((s, a) => s + (a.actual_amount - a.expected_amount), 0);
    return { total, critical, unacked, totalImpact };
  }, [anomalies]);

  function saveAlertConfig() {
    localStorage.setItem('cp_anomaly_config', JSON.stringify(alertConfig));
    setShowConfig(false);
  }

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="flex items-center justify-between mb-8">
          <div><Skeleton variant="text" className="w-40 h-7 mb-2" /><Skeleton variant="text" className="w-64 h-4" /></div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
        <div className="space-y-4 stagger-children"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
      </div>
    );
  }

  const filtered = filter === 'all' ? anomalies : anomalies.filter((a) => a.severity === filter);

  // Group anomalies by service for attribution
  const serviceBreakdown = useMemo(() => {
    const map = {};
    anomalies.forEach(a => {
      if (!map[a.service]) map[a.service] = { service: a.service, count: 0, impact: 0 };
      map[a.service].count++;
      map[a.service].impact += a.actual_amount - a.expected_amount;
    });
    return Object.values(map).sort((a, b) => b.impact - a.impact);
  }, [anomalies]);

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Anomalies" description="Unusual cost spikes detected across your connected providers" icon={AlertTriangle}>
        <div className="flex gap-1 p-1 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
          {['all', 'critical', 'warning', 'info'].map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className="px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-semibold transition-all capitalize"
              style={{ backgroundColor: filter === f ? 'var(--brand-600)' : 'transparent', color: filter === f ? 'white' : 'var(--color-text-secondary)' }}>
              {f}
            </button>
          ))}
        </div>
        <Button variant="secondary" size="sm" icon={Settings2} onClick={() => setShowConfig(true)}>Alert Config</Button>
      </PageHeader>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Anomalies" value={stats.total} icon={Activity} />
        <StatCard label="Critical" value={stats.critical} icon={AlertTriangle} trend={stats.critical > 0 ? 'up' : 'neutral'} trendValue={stats.critical > 0 ? 'Needs attention' : 'None'} />
        <StatCard label="Unacknowledged" value={stats.unacked} icon={Bell} />
        <StatCard label="Cost Impact" value={`$${stats.totalImpact.toFixed(0)}`} icon={DollarSign} trend="up" trendValue="Above expected" />
      </div>

      {/* Timeline Chart */}
      {anomalies.length > 0 && (
        <Card className="mb-6">
          <CardTitle>Anomaly Timeline (Last 7 Days)</CardTitle>
          <div style={{ height: 200 }} className="mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockTimelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="anomalies" name="anomalies" radius={[4, 4, 0, 0]}>
                  {mockTimelineData.map((entry, i) => (
                    <Cell key={i} fill={entry.anomalies >= 3 ? 'var(--color-error)' : entry.anomalies >= 1 ? 'var(--color-warning)' : 'var(--color-border)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {/* Service Attribution */}
      {serviceBreakdown.length > 0 && (
        <Card className="mb-6">
          <CardTitle>Cost Impact by Service</CardTitle>
          <div className="mt-4 space-y-3">
            {serviceBreakdown.map(s => (
              <div key={s.service} className="flex items-center gap-3">
                <span className="text-sm font-medium w-32 truncate" style={{ color: 'var(--color-text-primary)' }}>{s.service}</span>
                <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <div className="h-full rounded-full" style={{ width: `${Math.min((s.impact / Math.max(serviceBreakdown[0].impact, 1)) * 100, 100)}%`, backgroundColor: 'var(--color-error)' }} />
                </div>
                <span className="text-sm font-semibold w-24 text-right" style={{ color: 'var(--color-error)' }}>+${s.impact.toFixed(2)}</span>
                <Badge variant="neutral">{s.count}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Alert Configuration Modal */}
      <Modal open={showConfig} onClose={() => setShowConfig(false)} title="Alert Configuration">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Critical Threshold (% deviation)</label>
            <input type="number" value={alertConfig.criticalThreshold} onChange={e => setAlertConfig({ ...alertConfig, criticalThreshold: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm outline-none"
              style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Warning Threshold (% deviation)</label>
            <input type="number" value={alertConfig.warningThreshold} onChange={e => setAlertConfig({ ...alertConfig, warningThreshold: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm outline-none"
              style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
          </div>
          <div className="space-y-3">
            {[{ key: 'emailEnabled', label: 'Email Notifications' }, { key: 'slackEnabled', label: 'Slack Notifications' }, { key: 'autoAcknowledge', label: 'Auto-acknowledge info alerts' }].map(opt => (
              <label key={opt.key} className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={alertConfig[opt.key]} onChange={e => setAlertConfig({ ...alertConfig, [opt.key]: e.target.checked })}
                  className="rounded accent-[var(--brand-600)]" />
                <span className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{opt.label}</span>
              </label>
            ))}
          </div>
          <div className="flex gap-2 justify-end mt-4">
            <Button variant="secondary" onClick={() => setShowConfig(false)}>Cancel</Button>
            <Button onClick={saveAlertConfig}>Save Configuration</Button>
          </div>
        </div>
      </Modal>

      {/* Anomaly Detail Modal */}
      <Modal open={!!selectedAnomaly} onClose={() => setSelectedAnomaly(null)} title="Anomaly Details">
        {selectedAnomaly && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant={severityVariant[selectedAnomaly.severity]}>{selectedAnomaly.severity.toUpperCase()}</Badge>
              <span className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>{selectedAnomaly.date}</span>
            </div>
            <div>
              <h3 className="font-semibold text-lg" style={{ color: 'var(--color-text-primary)' }}>{selectedAnomaly.service}</h3>
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                Cost deviated from expected range by {(selectedAnomaly.deviation_pct * 100).toFixed(0)}%
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Expected</p>
                <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>${selectedAnomaly.expected_amount.toFixed(2)}</p>
              </div>
              <div className="p-3 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Actual</p>
                <p className="text-lg font-bold" style={{ color: 'var(--color-error)' }}>${selectedAnomaly.actual_amount.toFixed(2)}</p>
              </div>
            </div>
            <div className="p-3 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
              <p className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-tertiary)' }}>Possible Root Causes</p>
              <ul className="text-sm space-y-1" style={{ color: 'var(--color-text-secondary)' }}>
                <li>• Increased API calls or data transfer</li>
                <li>• Auto-scaling triggered additional resources</li>
                <li>• New deployment or configuration change</li>
              </ul>
            </div>
            {!selectedAnomaly.acknowledged && (
              <Button className="w-full" onClick={() => { handleAcknowledge(selectedAnomaly.id); setSelectedAnomaly({ ...selectedAnomaly, acknowledged: true }); }}>
                Acknowledge Anomaly
              </Button>
            )}
          </div>
        )}
      </Modal>

      {/* Anomaly List */}
      {filtered.length === 0 ? (
        <EmptyState icon={CheckCircle} title="No anomalies detected" description="Your spending is within normal ranges across all connected providers. We'll alert you if anything unusual happens." />
      ) : (
        <div className="space-y-4 stagger-children">
          {filtered.map((anomaly) => (
            <Card key={anomaly.id} className={`cursor-pointer hover:shadow-md transition-shadow ${anomaly.acknowledged ? 'opacity-60' : ''}`}
              onClick={() => setSelectedAnomaly(anomaly)}>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: severityColor[anomaly.severity] }} />
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={severityVariant[anomaly.severity]}>{anomaly.severity.toUpperCase()}</Badge>
                      <span className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>{anomaly.date}</span>
                    </div>
                    <h3 className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{anomaly.service}</h3>
                    <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                      Expected <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>${anomaly.expected_amount.toFixed(2)}</span>
                      {' '}→ Actual <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>${anomaly.actual_amount.toFixed(2)}</span>
                      {' '}<span style={{ color: 'var(--color-error)' }} className="font-semibold">(+{(anomaly.deviation_pct * 100).toFixed(0)}%)</span>
                    </p>
                  </div>
                </div>
                {!anomaly.acknowledged ? (
                  <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); handleAcknowledge(anomaly.id); }}>Acknowledge</Button>
                ) : (
                  <Badge variant="success" icon={CheckCircle}>Acknowledged</Badge>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

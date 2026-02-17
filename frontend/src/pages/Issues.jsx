import { useState } from 'react';
import { ClipboardList, Plus, CheckCircle2, Clock, AlertCircle, Circle, DollarSign, ArrowUp, ArrowRight, ArrowDown } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/EmptyState';
import { StatCard } from '../components/ui/StatCard';

const PRIORITY_ICONS = { high: ArrowUp, medium: ArrowRight, low: ArrowDown };
const PRIORITY_COLORS = { high: 'error', medium: 'warning', low: 'info' };
const STATUS_ICONS = { open: Circle, 'in-progress': Clock, resolved: CheckCircle2 };
const STATUS_COLORS = { open: 'neutral', 'in-progress': 'warning', resolved: 'success' };

const DEFAULT_ISSUES = [
  { id: 1, title: 'Rightsize m5.xlarge EC2 instances', description: 'CPU utilization averaging 12% — downsize to m5.large', status: 'open', priority: 'high', assignee: 'alex@team.io', category: 'Rightsizing', estimatedSavings: 420, createdAt: '2026-02-10', source: 'Recommendation' },
  { id: 2, title: 'Delete unused EBS volumes', description: '3 unattached gp3 volumes in us-east-1', status: 'in-progress', priority: 'medium', assignee: 'jordan@team.io', category: 'Idle Resources', estimatedSavings: 120, createdAt: '2026-02-08', source: 'Recommendation' },
  { id: 3, title: 'Purchase Compute Savings Plan', description: 'Stable EC2 baseline qualifies for 1yr no-upfront SP', status: 'open', priority: 'high', assignee: 'alex@team.io', category: 'Financial Commitment', estimatedSavings: 890, createdAt: '2026-02-05', source: 'Manual' },
  { id: 4, title: 'Migrate gp2 to gp3 volumes', description: 'Generational upgrade saves ~20% on EBS costs', status: 'open', priority: 'medium', assignee: null, category: 'Generation Upgrade', estimatedSavings: 65, createdAt: '2026-02-12', source: 'Recommendation' },
  { id: 5, title: 'Investigate CloudFront spike', description: 'Anomaly detected: 3x normal egress on Feb 9', status: 'resolved', priority: 'high', assignee: 'jordan@team.io', category: 'Anomaly', estimatedSavings: 0, createdAt: '2026-02-09', source: 'Anomaly Alert' },
  { id: 6, title: 'Optimize S3 lifecycle policies', description: 'Move infrequent access data to S3-IA after 30 days', status: 'open', priority: 'low', assignee: null, category: 'Storage', estimatedSavings: 45, createdAt: '2026-02-14', source: 'Manual' },
];

export default function Issues() {
  const [issues, setIssues] = useState(DEFAULT_ISSUES);
  const [filter, setFilter] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newPriority, setNewPriority] = useState('medium');

  const filtered = filter === 'all' ? issues : issues.filter((i) => i.status === filter);
  const totalSavings = issues.filter((i) => i.status !== 'resolved').reduce((s, i) => s + i.estimatedSavings, 0);
  const openCount = issues.filter((i) => i.status === 'open').length;
  const inProgressCount = issues.filter((i) => i.status === 'in-progress').length;

  function updateStatus(id, newStatus) {
    setIssues(issues.map((i) => i.id === id ? { ...i, status: newStatus } : i));
  }

  function createIssue() {
    const issue = {
      id: Date.now(),
      title: newTitle || 'Untitled Issue',
      description: newDesc,
      status: 'open',
      priority: newPriority,
      assignee: null,
      category: 'Manual',
      estimatedSavings: 0,
      createdAt: new Date().toISOString().split('T')[0],
      source: 'Manual',
    };
    setIssues([issue, ...issues]);
    setShowCreate(false);
    setNewTitle(''); setNewDesc(''); setNewPriority('medium');
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Issues" description="Track and manage cost optimization tasks" icon={ClipboardList}>
        <Button size="sm" icon={Plus} onClick={() => setShowCreate(true)}>New Issue</Button>
      </PageHeader>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <StatCard icon={AlertCircle} label="Open" value={openCount} trendLabel="issues" />
        <StatCard icon={Clock} label="In Progress" value={inProgressCount} trendLabel="issues" />
        <StatCard icon={CheckCircle2} label="Resolved" value={issues.filter((i) => i.status === 'resolved').length} trendLabel="issues" />
        <StatCard icon={DollarSign} label="Potential Savings" value={`$${totalSavings}/mo`} trendLabel={`${openCount + inProgressCount} actionable`} />
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 p-1 rounded-[var(--radius-md)] mb-6 inline-flex" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
        {['all', 'open', 'in-progress', 'resolved'].map((s) => (
          <button key={s} onClick={() => setFilter(s)} className="px-4 py-2 rounded-[var(--radius-sm)] text-xs font-semibold transition-all capitalize" style={{ backgroundColor: filter === s ? 'var(--brand-600)' : 'transparent', color: filter === s ? 'white' : 'var(--color-text-secondary)' }}>
            {s === 'all' ? `All (${issues.length})` : `${s} (${issues.filter((i) => i.status === s).length})`}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={ClipboardList} title="No issues" description="No issues match the current filter." />
      ) : (
        <div className="space-y-3">
          {filtered.map((issue) => {
            const PriorityIcon = PRIORITY_ICONS[issue.priority];
            const StatusIcon = STATUS_ICONS[issue.status];
            return (
              <Card key={issue.id} className="animate-fadeInUp">
                <div className="flex items-start gap-4">
                  <StatusIcon size={20} style={{ color: `var(--color-${STATUS_COLORS[issue.status]}${issue.status === 'neutral' ? '' : '-text'})`, marginTop: 2 }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>{issue.title}</h3>
                      <Badge variant={PRIORITY_COLORS[issue.priority]} size="sm" icon={PriorityIcon}>{issue.priority}</Badge>
                      <Badge variant="neutral" size="sm">{issue.category}</Badge>
                      {issue.source !== 'Manual' && <Badge variant="brand" size="sm">{issue.source}</Badge>}
                    </div>
                    <p className="text-xs mb-2" style={{ color: 'var(--color-text-secondary)' }}>{issue.description}</p>
                    <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                      {issue.assignee && <span>→ {issue.assignee}</span>}
                      <span>{issue.createdAt}</span>
                      {issue.estimatedSavings > 0 && (
                        <span className="font-semibold" style={{ color: 'var(--color-success-text)' }}>Save ${issue.estimatedSavings}/mo</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    {issue.status === 'open' && (
                      <Button variant="ghost" size="sm" onClick={() => updateStatus(issue.id, 'in-progress')}>Start</Button>
                    )}
                    {issue.status === 'in-progress' && (
                      <Button variant="ghost" size="sm" onClick={() => updateStatus(issue.id, 'resolved')}>Resolve</Button>
                    )}
                    {issue.status === 'resolved' && (
                      <Button variant="ghost" size="sm" onClick={() => updateStatus(issue.id, 'open')}>Reopen</Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Issue">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Title</label>
            <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="e.g., Rightsize production instances" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} autoFocus />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Description</label>
            <textarea value={newDesc} onChange={(e) => setNewDesc(e.target.value)} placeholder="Details..." rows={3} className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm resize-none" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Priority</label>
            <div className="flex gap-2">
              {['low', 'medium', 'high'].map((p) => (
                <button key={p} onClick={() => setNewPriority(p)} className="px-3 py-1.5 rounded-[var(--radius-md)] text-xs font-semibold capitalize transition-all" style={{ backgroundColor: newPriority === p ? 'var(--brand-600)' : 'var(--color-surface-secondary)', color: newPriority === p ? 'white' : 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }}>
                  {p}
                </button>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button size="sm" onClick={createIssue}>Create Issue</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

import { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { GitBranch, Plus, ChevronRight, ChevronDown, Trash2, Edit3, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { StatCard } from '../components/ui/StatCard';

const CHART_COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-5)', 'var(--chart-6)'];
const chartTooltipStyle = { backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' };

const DEFAULT_SEGMENTS = [
  { id: '1', name: 'Engineering', parentId: null, filters: [{ key: 'team', value: 'backend,frontend,data' }], cost: 2450.80, children: [
    { id: '1a', name: 'Backend', parentId: '1', filters: [{ key: 'team', value: 'backend' }], cost: 1280.50, children: [] },
    { id: '1b', name: 'Frontend', parentId: '1', filters: [{ key: 'team', value: 'frontend' }], cost: 720.30, children: [] },
    { id: '1c', name: 'Data', parentId: '1', filters: [{ key: 'team', value: 'data' }], cost: 450.00, children: [] },
  ]},
  { id: '2', name: 'Infrastructure', parentId: null, filters: [{ key: 'team', value: 'infra,devops' }], cost: 1350.20, children: [
    { id: '2a', name: 'DevOps', parentId: '2', filters: [{ key: 'team', value: 'devops' }], cost: 580.10, children: [] },
    { id: '2b', name: 'Platform', parentId: '2', filters: [{ key: 'team', value: 'infra' }], cost: 770.10, children: [] },
  ]},
  { id: '3', name: 'Marketing', parentId: null, filters: [{ key: 'team', value: 'marketing' }], cost: 284.50, children: [] },
];

function SegmentRow({ segment, depth = 0, expanded, toggleExpand }) {
  const [isOpen, setIsOpen] = useState(expanded);
  const hasChildren = segment.children && segment.children.length > 0;

  return (
    <>
      <div
        className="flex items-center py-3 px-4 hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer"
        style={{ paddingLeft: `${depth * 24 + 16}px`, borderBottom: '1px solid var(--color-border-light)' }}
        onClick={() => hasChildren && setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {hasChildren ? (
            isOpen ? <ChevronDown size={16} style={{ color: 'var(--color-text-tertiary)' }} /> : <ChevronRight size={16} style={{ color: 'var(--color-text-tertiary)' }} />
          ) : (
            <div className="w-4" />
          )}
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CHART_COLORS[parseInt(segment.id) % CHART_COLORS.length] }} />
          <span className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>{segment.name}</span>
          {segment.filters.map((f, i) => (
            <Badge key={i} variant="neutral" size="sm">{f.key}={f.value}</Badge>
          ))}
        </div>
        <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>${segment.cost.toFixed(2)}</span>
      </div>
      {isOpen && hasChildren && segment.children.map((child) => (
        <SegmentRow key={child.id} segment={child} depth={depth + 1} expanded={false} />
      ))}
    </>
  );
}

export default function Segments() {
  const [segments, setSegments] = useState(DEFAULT_SEGMENTS);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTagKey, setNewTagKey] = useState('');
  const [newTagValue, setNewTagValue] = useState('');

  const totalAllocated = segments.reduce((s, seg) => s + seg.cost, 0);
  const totalSpend = 4285.30;
  const unallocated = totalSpend - totalAllocated;
  const allocationPct = ((totalAllocated / totalSpend) * 100).toFixed(1);

  const chartData = segments.map((s) => ({ name: s.name, cost: s.cost }));
  if (unallocated > 0) chartData.push({ name: 'Unallocated', cost: unallocated });

  function createSegment() {
    const seg = {
      id: Date.now().toString(),
      name: newName || 'New Segment',
      parentId: null,
      filters: newTagKey ? [{ key: newTagKey, value: newTagValue }] : [],
      cost: Math.random() * 500 + 50,
      children: [],
    };
    setSegments([...segments, seg]);
    setShowCreate(false);
    setNewName(''); setNewTagKey(''); setNewTagValue('');
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Cost Allocation" description="Allocate and attribute costs to teams, projects, and business units" icon={GitBranch}>
        <Button size="sm" icon={Plus} onClick={() => setShowCreate(true)}>New Segment</Button>
      </PageHeader>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
        <StatCard icon={GitBranch} label="Total Segments" value={segments.length} trendLabel={`${segments.reduce((s, seg) => s + seg.children.length, 0)} sub-segments`} />
        <StatCard label="Allocated" value={`$${totalAllocated.toFixed(2)}`} trendLabel={`${allocationPct}% of total`} />
        <StatCard label="Unallocated" value={`$${unallocated.toFixed(2)}`} trendLabel={unallocated > 0 ? 'Needs attention' : 'Fully allocated'} trend={unallocated > 0 ? 5 : -5} />
        <StatCard label="Total Spend" value={`$${totalSpend.toFixed(2)}`} trendLabel="Current month" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Segment tree */}
        <div className="lg:col-span-2">
          <Card padding={false}>
            <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--color-border)' }}>
              <CardTitle>Segment Hierarchy</CardTitle>
              {unallocated > 0 && (
                <div className="flex items-center gap-1.5 text-xs font-medium" style={{ color: 'var(--color-warning-text)' }}>
                  <AlertCircle size={14} />
                  ${unallocated.toFixed(2)} unallocated
                </div>
              )}
            </div>
            {segments.map((seg) => (
              <SegmentRow key={seg.id} segment={seg} depth={0} expanded={true} />
            ))}
          </Card>
        </div>

        {/* Chart */}
        <Card>
          <CardTitle className="mb-4">Cost Distribution</CardTitle>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical">
              <XAxis type="number" tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} width={90} />
              <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`$${v.toFixed(2)}`, 'Cost']} />
              <Bar dataKey="cost" radius={[0, 4, 4, 0]}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={i === chartData.length - 1 && unallocated > 0 ? 'var(--color-text-tertiary)' : CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Segment">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Name</label>
            <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g., Engineering" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} autoFocus />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Tag Key</label>
              <input value={newTagKey} onChange={(e) => setNewTagKey(e.target.value)} placeholder="e.g., team" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Tag Value</label>
              <input value={newTagValue} onChange={(e) => setNewTagValue(e.target.value)} placeholder="e.g., backend" className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button size="sm" onClick={createSegment}>Create Segment</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

import { useState, useMemo } from 'react';
import { Server, Search, Filter, ArrowUpDown, ExternalLink, ChevronDown, Tag } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { StatCard } from '../components/ui/StatCard';

const MOCK_RESOURCES = [
  { id: 'i-0a1b2c3d4e5f6', type: 'EC2 Instance', service: 'Amazon EC2', region: 'us-east-1', instanceType: 'm5.xlarge', dailyCost: 4.61, monthlyCost: 138.24, status: 'running', tags: { env: 'production', team: 'backend' } },
  { id: 'i-1b2c3d4e5f6a7', type: 'EC2 Instance', service: 'Amazon EC2', region: 'us-east-1', instanceType: 't3.medium', dailyCost: 1.01, monthlyCost: 30.37, status: 'running', tags: { env: 'staging', team: 'frontend' } },
  { id: 'db-prod-primary', type: 'RDS Instance', service: 'Amazon RDS', region: 'us-east-1', instanceType: 'db.r5.large', dailyCost: 6.91, monthlyCost: 207.36, status: 'available', tags: { env: 'production', team: 'data' } },
  { id: 'db-replica-01', type: 'RDS Instance', service: 'Amazon RDS', region: 'us-west-2', instanceType: 'db.r5.large', dailyCost: 6.91, monthlyCost: 207.36, status: 'available', tags: { env: 'production', team: 'data' } },
  { id: 's3-assets-prod', type: 'S3 Bucket', service: 'Amazon S3', region: 'us-east-1', instanceType: 'Standard', dailyCost: 0.85, monthlyCost: 25.50, status: 'active', tags: { env: 'production', team: 'frontend' } },
  { id: 's3-logs-archive', type: 'S3 Bucket', service: 'Amazon S3', region: 'us-east-1', instanceType: 'Glacier', dailyCost: 0.12, monthlyCost: 3.60, status: 'active', tags: { env: 'production', team: 'devops' } },
  { id: 'lambda-api-handler', type: 'Lambda Function', service: 'AWS Lambda', region: 'us-east-1', instanceType: '512MB', dailyCost: 0.34, monthlyCost: 10.20, status: 'active', tags: { env: 'production', team: 'backend' } },
  { id: 'nat-0a1b2c3d', type: 'NAT Gateway', service: 'Amazon VPC', region: 'us-east-1', instanceType: 'NAT', dailyCost: 3.24, monthlyCost: 97.20, status: 'available', tags: { env: 'production', team: 'infra' } },
  { id: 'elb-api-prod', type: 'Load Balancer', service: 'Elastic Load Balancing', region: 'us-east-1', instanceType: 'ALB', dailyCost: 0.68, monthlyCost: 20.16, status: 'active', tags: { env: 'production', team: 'backend' } },
  { id: 'ebs-vol-0123', type: 'EBS Volume', service: 'Amazon EBS', region: 'us-east-1', instanceType: 'gp3 500GB', dailyCost: 1.33, monthlyCost: 40.00, status: 'in-use', tags: { env: 'production', team: 'backend' } },
  { id: 'cf-dist-E1A2B3', type: 'Distribution', service: 'Amazon CloudFront', region: 'global', instanceType: 'PriceClass_100', dailyCost: 0.45, monthlyCost: 13.50, status: 'deployed', tags: { env: 'production', team: 'frontend' } },
  { id: 'elasticache-prod', type: 'Cache Cluster', service: 'Amazon ElastiCache', region: 'us-east-1', instanceType: 'cache.r6g.large', dailyCost: 4.03, monthlyCost: 120.96, status: 'available', tags: { env: 'production', team: 'backend' } },
];

const SERVICES = [...new Set(MOCK_RESOURCES.map((r) => r.service))];
const REGIONS = [...new Set(MOCK_RESOURCES.map((r) => r.region))];

export default function Resources() {
  const [search, setSearch] = useState('');
  const [serviceFilter, setServiceFilter] = useState('all');
  const [regionFilter, setRegionFilter] = useState('all');
  const [sortField, setSortField] = useState('monthlyCost');
  const [sortDir, setSortDir] = useState('desc');
  const [selectedResource, setSelectedResource] = useState(null);

  const filtered = useMemo(() => {
    let data = MOCK_RESOURCES;
    if (search) data = data.filter((r) => r.id.toLowerCase().includes(search.toLowerCase()) || r.type.toLowerCase().includes(search.toLowerCase()) || r.service.toLowerCase().includes(search.toLowerCase()));
    if (serviceFilter !== 'all') data = data.filter((r) => r.service === serviceFilter);
    if (regionFilter !== 'all') data = data.filter((r) => r.region === regionFilter);
    data = [...data].sort((a, b) => sortDir === 'asc' ? (a[sortField] > b[sortField] ? 1 : -1) : (a[sortField] < b[sortField] ? 1 : -1));
    return data;
  }, [search, serviceFilter, regionFilter, sortField, sortDir]);

  const totalMonthly = MOCK_RESOURCES.reduce((s, r) => s + r.monthlyCost, 0);
  const totalDaily = MOCK_RESOURCES.reduce((s, r) => s + r.dailyCost, 0);

  function toggleSort(field) {
    if (sortField === field) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    else { setSortField(field); setSortDir('desc'); }
  }

  if (selectedResource) {
    const r = selectedResource;
    return (
      <div className="animate-fadeIn">
        <PageHeader title={r.id} description={`${r.type} · ${r.service}`} icon={Server}>
          <Button variant="ghost" size="sm" onClick={() => setSelectedResource(null)}>← Back</Button>
        </PageHeader>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard icon={Server} label="Monthly Cost" value={`$${r.monthlyCost.toFixed(2)}`} trendLabel={`$${r.dailyCost.toFixed(2)}/day`} />
          <StatCard label="Region" value={r.region} trendLabel={r.instanceType} />
          <StatCard label="Status" value={r.status} trendLabel={r.type} />
        </div>
        <Card>
          <CardTitle className="mb-4">Tags</CardTitle>
          <div className="flex flex-wrap gap-2">
            {Object.entries(r.tags).map(([k, v]) => (
              <Badge key={k} variant="neutral" icon={Tag}>{k}: {v}</Badge>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Resource Inventory" description={`${MOCK_RESOURCES.length} active resources across ${REGIONS.length} regions`} icon={Server} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard icon={Server} label="Total Resources" value={MOCK_RESOURCES.length} trendLabel={`${SERVICES.length} services`} />
        <StatCard label="Monthly Cost" value={`$${totalMonthly.toFixed(2)}`} trendLabel={`$${totalDaily.toFixed(2)}/day`} />
        <StatCard label="Top Service" value={MOCK_RESOURCES.sort((a, b) => b.monthlyCost - a.monthlyCost)[0]?.service} />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search resources..." className="w-full pl-9 pr-3 py-2 rounded-[var(--radius-md)] text-sm" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }} />
        </div>
        <select value={serviceFilter} onChange={(e) => setServiceFilter(e.target.value)} className="px-3 py-2 text-sm rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
          <option value="all">All Services</option>
          {SERVICES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)} className="px-3 py-2 text-sm rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
          <option value="all">All Regions</option>
          {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <Badge variant="neutral">{filtered.length} results</Badge>
      </div>

      {/* Table */}
      <Card padding={false}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                <th className="px-6 py-3 font-semibold">Resource</th>
                <th className="px-6 py-3 font-semibold">Service</th>
                <th className="px-6 py-3 font-semibold">Region</th>
                <th className="px-6 py-3 font-semibold">Type</th>
                <th className="px-6 py-3 font-semibold text-right cursor-pointer" onClick={() => toggleSort('monthlyCost')}>
                  <span className="inline-flex items-center gap-1">Monthly <ArrowUpDown size={12} /></span>
                </th>
                <th className="px-6 py-3 font-semibold text-right cursor-pointer" onClick={() => toggleSort('dailyCost')}>
                  <span className="inline-flex items-center gap-1">Daily <ArrowUpDown size={12} /></span>
                </th>
                <th className="px-6 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <tr key={r.id} onClick={() => setSelectedResource(r)} className="cursor-pointer transition-colors hover:bg-[var(--color-surface-hover)]" style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td className="px-6 py-3">
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{r.id}</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{r.type}</p>
                  </td>
                  <td className="px-6 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{r.service}</td>
                  <td className="px-6 py-3"><Badge variant="neutral" size="sm">{r.region}</Badge></td>
                  <td className="px-6 py-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{r.instanceType}</td>
                  <td className="px-6 py-3 text-sm text-right font-semibold" style={{ color: 'var(--color-text-primary)' }}>${r.monthlyCost.toFixed(2)}</td>
                  <td className="px-6 py-3 text-sm text-right" style={{ color: 'var(--color-text-tertiary)' }}>${r.dailyCost.toFixed(2)}</td>
                  <td className="px-6 py-3"><Badge variant={r.status === 'running' || r.status === 'available' || r.status === 'active' || r.status === 'deployed' || r.status === 'in-use' ? 'success' : 'warning'} size="sm">{r.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
